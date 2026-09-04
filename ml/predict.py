import joblib
import pandas as pd

model = joblib.load("ml/risk_model.joblib")


def predict_risk(transaction):
    data = pd.DataFrame([transaction])

    risk_score = model.predict_proba(data)[0][1]
    prediction = model.predict(data)[0]

    return {
        "risk_score": round(float(risk_score), 4),
        "is_suspicious": bool(prediction)
    }


if __name__ == "__main__":
    sample_transaction = {
        "amount": 4500,
        "payment_method": "UPI",
        "status": "SUCCESS",
        "country": "IN",
        "failed_attempts": 4,
        "account_age_days": 30,
        "hour": 2,
        "user_txn_count_1h": 8
    }

    result = predict_risk(sample_transaction)

    print(result)