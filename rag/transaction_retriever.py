import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set.")

engine = create_engine(DATABASE_URL)


def get_transaction_context(transaction_id: str):
    """
    Retrieve live investigation context from PostgreSQL.
    """

    transaction_query = text("""
        SELECT
            t.id,
            t.transaction_id,
            t.user_id,
            t.amount,
            t.currency,
            t.payment_method,
            t.merchant_id,
            t.transaction_timestamp,
            t.status,
            t.country,
            t.device_id,
            t.ip_id,
            t.failed_attempts,
            t.account_age_days,
            t.hour,
            t.user_txn_count_1h,
            r.risk_score,
            r.risk_level,
            r.model_version
        FROM transactions t
        LEFT JOIN risk_assessments r
            ON r.transaction_id = t.id
        WHERE t.transaction_id = :transaction_id
        ORDER BY r.created_at DESC NULLS LAST
        LIMIT 1
    """)

    with engine.connect() as connection:

        transaction = connection.execute(
            transaction_query,
            {"transaction_id": transaction_id}
        ).mappings().first()

        if not transaction:
            return None

        transaction = dict(transaction)

        user_id = transaction["user_id"]

        history_query = text("""
            SELECT
                transaction_id,
                amount,
                payment_method,
                status,
                country,
                failed_attempts,
                transaction_timestamp
            FROM transactions
            WHERE user_id = :user_id
              AND transaction_id != :transaction_id
            ORDER BY transaction_timestamp DESC
            LIMIT 10
        """)

        history = connection.execute(
            history_query,
            {
                "user_id": user_id,
                "transaction_id": transaction_id
            }
        ).mappings().all()

        history = [dict(row) for row in history]

        cases_query = text("""
            SELECT
                c.id,
                t.transaction_id,
                c.status,
                c.priority,
                c.investigation_summary,
                c.created_at
            FROM cases c
            JOIN transactions t
                ON c.transaction_id = t.id
            WHERE t.user_id = :user_id
            ORDER BY c.created_at DESC
            LIMIT 5
        """)

        previous_cases = connection.execute(
            cases_query,
            {"user_id": user_id}
        ).mappings().all()

        previous_cases = [
            dict(row)
            for row in previous_cases
        ]

    return {
        "transaction": transaction,
        "transaction_history": history,
        "previous_cases": previous_cases
    }


if __name__ == "__main__":

    transaction_id = "TXN00504"

    print("\n" + "=" * 60)
    print("DYNAMIC TRANSACTION CONTEXT")
    print("=" * 60)

    context = get_transaction_context(transaction_id)

    if not context:
        print(f"Transaction {transaction_id} not found.")

    else:

        print("\nCurrent Transaction:")
        print(context["transaction"])

        print("\nRecent Transaction History:")

        for transaction in context["transaction_history"]:
            print(transaction)

        print("\nPrevious Cases:")

        for case in context["previous_cases"]:
            print(case)