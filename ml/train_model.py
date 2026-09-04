import pandas as pd

import joblib

from sklearn.model_selection import train_test_split

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

from sklearn.metrics import classification_report, confusion_matrix

df = pd.read_csv("risk_transactions_500.csv")

features = [
    "amount",
    "payment_method",
    "status",
    "country",
    "failed_attempts",
    "account_age_days",
    "hour",
    "user_txn_count_1h"
]

X = df[features]
y = df["is_suspicious"]

print("Features:")
print(X.head())

print("\nTarget:")
print(y.head())


train_df = df[df["dataset_split"] == "train"]
test_df = df[df["dataset_split"] == "test"]

X_train = train_df[features]
y_train = train_df["is_suspicious"]

X_test = test_df[features]
y_test = test_df["is_suspicious"]

print("\nTraining data:", X_train.shape)
print("Testing data:", X_test.shape)


categorical_features = [
    "payment_method",
    "status",
    "country"
]

numeric_features = [
    "amount",
    "failed_attempts",
    "account_age_days",
    "hour",
    "user_txn_count_1h"
]

preprocessor = ColumnTransformer(
    transformers=[
        ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ("numeric", "passthrough", numeric_features)
    ]
)

X_train_encoded = preprocessor.fit_transform(X_train)
X_test_encoded = preprocessor.transform(X_test)

print("\nEncoded training shape:", X_train_encoded.shape)
print("Encoded testing shape:", X_test_encoded.shape)

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced"
    ))
])

model.fit(X_train, y_train)

print("\nModel trained successfully!")

y_pred = model.predict(X_test)

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

risk_scores = model.predict_proba(X_test)[:, 1]

print("\nRisk Scores:")
print(risk_scores[:10])

joblib.dump(model, "ml/risk_model.joblib")

print("\nModel saved successfully!")