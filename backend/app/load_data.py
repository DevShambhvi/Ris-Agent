import pandas as pd  # type: ignore[import-not-found]
from sqlalchemy import create_engine, text  # type: ignore[import-not-found]
from dotenv import load_dotenv  # type: ignore[import-not-found]
import os

# Load .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to PostgreSQL
engine = create_engine(DATABASE_URL)

# Read CSV
df = pd.read_csv("risk_transactions_500.csv")

# Convert timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Insert transactions
with engine.begin() as connection:

    for _, row in df.iterrows():

        connection.execute(
            text("""
                INSERT INTO transactions (
                    transaction_id,
                    user_id,
                    amount,
                    currency,
                    payment_method,
                    merchant_id,
                    transaction_timestamp,
                    status,
                    country,
                    device_id,
                    ip_id,
                    failed_attempts,
                    account_age_days,
                    hour,
                    user_txn_count_1h,
                    is_suspicious,
                    risk_reason
                )
                VALUES (
                    :transaction_id,
                    :user_id,
                    :amount,
                    :currency,
                    :payment_method,
                    :merchant_id,
                    :timestamp,
                    :status,
                    :country,
                    :device_id,
                    :ip_id,
                    :failed_attempts,
                    :account_age_days,
                    :hour,
                    :user_txn_count_1h,
                    :is_suspicious,
                    :risk_reason
                )
            """),
            {
                "transaction_id": row["transaction_id"],
                "user_id": int(row["user_id"]),
                "amount": float(row["amount"]),
                "currency": row["currency"],
                "payment_method": row["payment_method"],
                "merchant_id": row["merchant_id"],
                "timestamp": row["timestamp"],
                "status": row["status"],
                "country": row["country"],
                "device_id": row["device_id"],
                "ip_id": row["ip_id"],
                "failed_attempts": int(row["failed_attempts"]),
                "account_age_days": int(row["account_age_days"]),
                "hour": int(row["hour"]),
                "user_txn_count_1h": int(row["user_txn_count_1h"]),
                "is_suspicious": bool(row["is_suspicious"]),
                "risk_reason": row["risk_reason"],
            }
        )

print("500 transactions loaded successfully!")