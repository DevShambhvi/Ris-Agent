import os
import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

model = joblib.load("ml/risk_model.joblib")

FEATURES = [
    "amount",
    "payment_method",
    "status",
    "country",
    "failed_attempts",
    "account_age_days",
    "hour",
    "user_txn_count_1h"
]

MODEL_VERSION = "random_forest_v1"


def process_transaction(transaction_id):
    """
    Run the ML risk detector for one transaction
    and store/update its risk assessment.
    """

    query = text("""
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
        WHERE transaction_id = :transaction_id
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"transaction_id": transaction_id}
        ).mappings().first()

    if not result:
        raise ValueError(
            f"Transaction {transaction_id} not found."
        )

    transaction = dict(result)

    df = pd.DataFrame([transaction])

    risk_score = float(
        model.predict_proba(df[FEATURES])[:, 1][0]
    )

    prediction = bool(
        model.predict(df[FEATURES])[0]
    )

    risk_level = (
        "HIGH"
        if risk_score >= 0.7
        else "MEDIUM"
        if risk_score >= 0.3
        else "LOW"
    )

    insert_query = text("""
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
    """)

    with engine.begin() as connection:
        connection.execute(
            insert_query,
            {
                "transaction_id": transaction["id"],
                "risk_score": risk_score,
                "risk_level": risk_level,
                "model_version": MODEL_VERSION
            }
        )

    return {
        "transaction_id": transaction_id,
        "risk_score": round(risk_score, 4),
        "risk_level": risk_level,
        "is_suspicious": prediction,
        "model_version": MODEL_VERSION
    }


if __name__ == "__main__":

    result = process_transaction("TXN00501")

    print("\nML Risk Assessment:")
    print(f"  Transaction:  {result['transaction_id']}")
    print(f"  Risk Score:   {result['risk_score']}")
    print(f"  Risk Level:   {result['risk_level']}")
    print(f"  Suspicious:   {result['is_suspicious']}")
    print(f"  Model:        {result['model_version']}")