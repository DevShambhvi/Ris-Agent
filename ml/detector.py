import os
import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

model = joblib.load("ml/risk_model.joblib")

query = """
SELECT
    id,
    amount,
    payment_method,
    status,
    country,
    failed_attempts,
    account_age_days,
    hour,
    user_txn_count_1h
FROM transactions
"""

df = pd.read_sql(query, engine)

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

risk_scores = model.predict_proba(df[features])[:, 1]
predictions = model.predict(df[features])

with engine.begin() as connection:
    for i in range(len(df)):
        connection.execute(
            text("""
                INSERT INTO risk_assessments (
                    transaction_id,
                    risk_score,
                    risk_level,
                    model_version
                )
                VALUES (
                    :transaction_id,
                    :risk_score,
                    :risk_level,
                    :model_version
                )
            """),
            {
                "transaction_id": int(df.iloc[i]["id"]),
                "risk_score": float(risk_scores[i]),
                "risk_level": (
                    "HIGH" if risk_scores[i] >= 0.7
                    else "MEDIUM" if risk_scores[i] >= 0.3
                    else "LOW"
                ),
                "model_version": "random_forest_v1"
            }
        )

print(f"Processed {len(df)} transactions.")
print("Risk assessments stored successfully!")