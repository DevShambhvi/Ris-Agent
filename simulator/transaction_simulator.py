import os
import random
from datetime import datetime, timedelta

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Configuration
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

engine = create_engine(DATABASE_URL)

TOTAL_TRANSACTIONS = 10_000
SUSPICIOUS_RATIO = 0.10

RANDOM_SEED = 42

PAYMENT_METHODS = [
    "UPI",
    "CARD",
    "NETBANKING",
]

COUNTRIES = [
    "IN",
    "US",
    "SG",
    "AE",
]

MERCHANTS = [
    "MERCHANT001",
    "MERCHANT002",
    "MERCHANT003",
    "MERCHANT004",
    "MERCHANT005",
]

# Helper functions
def generate_normal_transaction(user_id, transaction_time):
    """
    Generate a realistic normal payment transaction.
    """

    payment_method = random.choice(PAYMENT_METHODS)

    amount = round(random.uniform(100, 2500), 2)

    country = "IN"

    failed_attempts = random.choice(
        [0, 0, 0, 0, 1]
    )

    account_age_days = random.randint(60, 1500)

    hour = transaction_time.hour

    user_txn_count_1h = random.randint(0, 4)

    status = "SUCCESS"

    return {
        "user_id": user_id,
        "amount": amount,
        "currency": "INR",
        "payment_method": payment_method,
        "merchant_id": random.choice(MERCHANTS),
        "transaction_timestamp": transaction_time,
        "status": status,
        "country": country,
        "device_id": f"DEV{user_id:04d}",
        "ip_id": f"IP{user_id:04d}",
        "failed_attempts": failed_attempts,
        "account_age_days": account_age_days,
        "hour": hour,
        "user_txn_count_1h": user_txn_count_1h,
        "is_suspicious": False,
        "risk_reason": None,
    }


def generate_suspicious_transaction(user_id, transaction_time):
    """
    Generate a suspicious payment pattern.
    """

    pattern = random.choice([
        "velocity",
        "failed_attempts",
        "high_amount",
        "new_account",
        "combined",
    ])

    payment_method = random.choice(PAYMENT_METHODS)

    amount = round(random.uniform(100, 2500), 2)
    failed_attempts = random.randint(0, 1)
    account_age_days = random.randint(60, 1500)
    user_txn_count_1h = random.randint(0, 4)
    country = "IN"

    risk_reason = ""

    # Pattern 1: High transaction velocity
    if pattern == "velocity":

        user_txn_count_1h = random.randint(5, 15)

        risk_reason = "HIGH_VELOCITY"

    # Pattern 2: Repeated payment failures
    elif pattern == "failed_attempts":

        failed_attempts = random.randint(3, 7)

        status = "FAILED"

        risk_reason = "REPEATED_FAILURES"

    # Pattern 3: Unusually high amount
    elif pattern == "high_amount":

        amount = round(random.uniform(5000, 25000), 2)

        risk_reason = "HIGH_AMOUNT"

    # Pattern 4: New account activity
    elif pattern == "new_account":

        account_age_days = random.randint(1, 20)

        amount = round(random.uniform(3000, 15000), 2)

        risk_reason = "NEW_ACCOUNT"

    # Pattern 5: Multiple risk signals
    else:

        amount = round(random.uniform(8000, 25000), 2)

        failed_attempts = random.randint(3, 7)

        account_age_days = random.randint(1, 15)

        user_txn_count_1h = random.randint(7, 15)

        risk_reason = "MULTIPLE_RISK_SIGNALS"

    # Geographic anomaly is added to some suspicious
    # transactions.

    if random.random() < 0.25:

        country = random.choice([
            "US",
            "SG",
            "AE",
        ])

        risk_reason += "_LOCATION"

    # Status defaults to SUCCESS unless explicitly failed.

    status = locals().get("status", "SUCCESS")

    return {
        "user_id": user_id,
        "amount": amount,
        "currency": "INR",
        "payment_method": payment_method,
        "merchant_id": random.choice(MERCHANTS),
        "transaction_timestamp": transaction_time,
        "status": status,
        "country": country,
        "device_id": f"DEV{user_id:04d}",
        "ip_id": f"IP{user_id:04d}",
        "failed_attempts": failed_attempts,
        "account_age_days": account_age_days,
        "hour": transaction_time.hour,
        "user_txn_count_1h": user_txn_count_1h,
        "is_suspicious": True,
        "risk_reason": risk_reason,
    }

# Generate transactions
def generate_transactions(total_transactions):
    """
    Generate the complete synthetic transaction dataset.
    """

    transactions = []

    suspicious_count = int(
        total_transactions * SUSPICIOUS_RATIO
    )

    normal_count = total_transactions - suspicious_count

    print("\nGenerating transaction dataset...")
    print(f"Total transactions : {total_transactions}")
    print(f"Normal             : {normal_count}")
    print(f"Suspicious         : {suspicious_count}")

    base_time = datetime.now() - timedelta(days=30)

    # Normal transactions
    for _ in range(normal_count):

        user_id = random.randint(1, 80)

        transaction_time = (
            base_time
            + timedelta(
                seconds=random.randint(
                    0,
                    30 * 24 * 60 * 60
                )
            )
        )

        transaction = generate_normal_transaction(
            user_id,
            transaction_time
        )

        transactions.append(transaction)

    # Suspicious transactions
    for _ in range(suspicious_count):

        user_id = random.randint(1, 80)

        transaction_time = (
            base_time
            + timedelta(
                seconds=random.randint(
                    0,
                    30 * 24 * 60 * 60
                )
            )
        )

        transaction = generate_suspicious_transaction(
            user_id,
            transaction_time
        )

        transactions.append(transaction)

    # Shuffle so suspicious transactions aren't grouped
    # together.

    random.shuffle(transactions)

    return transactions

# Insert into PostgreSQL
def insert_transactions(transactions):
    """
    Insert generated transactions into PostgreSQL.
    """

    print("\nPreparing database insert...")

    # Reserve PostgreSQL IDs safely.

    with engine.begin() as connection:

        sequence_name = connection.execute(
            text("""
                SELECT pg_get_serial_sequence(
                    'transactions',
                    'id'
                )
            """)
        ).scalar()

        if not sequence_name:
            raise ValueError(
                "Could not find PostgreSQL sequence for transactions.id"
            )

        reserved_ids = connection.execute(
            text(f"""
                SELECT nextval('{sequence_name}')
                FROM generate_series(
                    1,
                    :count
                )
            """),
            {
                "count": len(transactions)
            }
        ).scalars().all()

    if len(reserved_ids) != len(transactions):

        raise ValueError(
            "Could not reserve transaction IDs."
        )

    rows = []

    for transaction_id, transaction in zip(
        reserved_ids,
        transactions
    ):

        rows.append({
            "id": transaction_id,
            "transaction_id": f"TXN{transaction_id:05d}",
            **transaction,
        })

    insert_query = text("""
        INSERT INTO transactions (
            id,
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
            :id,
            :transaction_id,
            :user_id,
            :amount,
            :currency,
            :payment_method,
            :merchant_id,
            :transaction_timestamp,
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
    """)

    print(
        f"Inserting {len(rows):,} transactions..."
    )

    # Insert in batches so memory usage stays reasonable.

    batch_size = 1000

    with engine.begin() as connection:

        for start in range(
            0,
            len(rows),
            batch_size
        ):

            batch = rows[
                start:start + batch_size
            ]

            connection.execute(
                insert_query,
                batch
            )

            inserted = min(
                start + batch_size,
                len(rows)
            )

            print(
                f"Inserted {inserted:,}/{len(rows):,}"
            )

    return rows

# Verification
def verify_database():
    """
    Verify that transactions were inserted correctly.
    """

    print("\nVerifying database...")

    with engine.connect() as connection:

        total = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM transactions
            """)
        ).scalar()

        suspicious = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM transactions
                WHERE is_suspicious = TRUE
            """)
        ).scalar()

        normal = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM transactions
                WHERE is_suspicious = FALSE
            """)
        ).scalar()

        recent = connection.execute(
            text("""
                SELECT
                    transaction_id,
                    amount,
                    payment_method,
                    status,
                    country,
                    failed_attempts,
                    account_age_days,
                    user_txn_count_1h,
                    is_suspicious,
                    risk_reason
                FROM transactions
                ORDER BY id DESC
                LIMIT 5
            """)
        ).mappings().all()

    print("\nDatabase verification:")
    print(f"Total transactions : {total:,}")
    print(f"Normal             : {normal:,}")
    print(f"Suspicious         : {suspicious:,}")

    print("\nLatest transactions:")

    for row in recent:

        print(
            f"{row['transaction_id']} | "
            f"₹{row['amount']} | "
            f"{row['payment_method']} | "
            f"{row['status']} | "
            f"{row['country']} | "
            f"failed={row['failed_attempts']} | "
            f"velocity={row['user_txn_count_1h']} | "
            f"suspicious={row['is_suspicious']} | "
            f"reason={row['risk_reason']}"
        )

# Main
def main():

    random.seed(RANDOM_SEED)

    print("=" * 60)
    print("RIS-AGENT TRANSACTION SIMULATOR")
    print("=" * 60)

    transactions = generate_transactions(
        TOTAL_TRANSACTIONS
    )

    insert_transactions(
        transactions
    )

    verify_database()

    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()