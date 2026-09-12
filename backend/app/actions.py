from sqlalchemy import text

from .database import engine

# ALLOWED ACTIONS 
ALLOWED_ACTIONS = {
    "ALLOW",
    "REVIEW_TRANSACTION",
    "BLOCK_TRANSACTION"
}

# MAP ACTION → EXPECTED TRANSACTION STATUS

EXPECTED_STATUS = {
    "ALLOW": "SUCCESS",
    "REVIEW_TRANSACTION": "UNDER_REVIEW",
    "BLOCK_TRANSACTION": "BLOCKED"
}

# EXECUTE + VERIFY TRANSACTION ACTION
def apply_transaction_action(
    transaction_id: str,
    action: str
):
    """
    Execute a transaction action and independently verify
    that the expected database state was reached.
    """

    # 1. Validate action
    if action not in ALLOWED_ACTIONS:

        raise ValueError(
            f"Invalid action: {action}"
        )

    expected_status = EXPECTED_STATUS[action]

    # 2. Execute action
    update_query = text("""
        UPDATE transactions
        SET status = :status
        WHERE transaction_id = :transaction_id
        RETURNING
            transaction_id,
            status
    """)

    with engine.begin() as connection:

        result = connection.execute(
            update_query,
            {
                "status": expected_status,
                "transaction_id": transaction_id
            }
        ).mappings().first()

    # 3. Transaction not found
    if not result:

        raise ValueError(
            "Transaction not found"
        )

    executed_status = result["status"]

    # 4. Independently verify database state
    verification_query = text("""
        SELECT
            transaction_id,
            status
        FROM transactions
        WHERE transaction_id = :transaction_id
    """)

    with engine.connect() as connection:

        verification = connection.execute(
            verification_query,
            {
                "transaction_id": transaction_id
            }
        ).mappings().first()

    # 5. Verification failed
    if not verification:

        return {
            "transaction_id": transaction_id,
            "action": action,
            "status": executed_status,
            "expected_status": expected_status,
            "verified": False,
            "verification_status": "FAILED",
            "message": (
                "Action executed but transaction "
                "could not be verified."
            )
        }

    actual_status = verification["status"]

    # 6. Compare expected vs actual state
    verified = (
        actual_status == expected_status
    )

    if verified:

        return {
            "transaction_id": transaction_id,
            "action": action,
            "status": actual_status,
            "expected_status": expected_status,
            "verified": True,
            "verification_status": "VERIFIED",
            "message": (
                f"Action {action} executed and "
                f"verified successfully."
            )
        }

    # 7. Unexpected state
    return {
        "transaction_id": transaction_id,
        "action": action,
        "status": actual_status,
        "expected_status": expected_status,
        "verified": False,
        "verification_status": "FAILED",
        "message": (
            "Action execution completed, but the "
            "resulting transaction state did not "
            "match the expected state."
        )
    }

# MANUAL TESTING 
if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("ACTION EXECUTION + VERIFICATION TEST")
    print("=" * 70)

    # Test transaction
    transaction_id = "TXN00504"

    result = apply_transaction_action(
        transaction_id,
        "REVIEW_TRANSACTION"
    )

    print("\nTransaction:")
    print(result["transaction_id"])

    print("\nAction:")
    print(result["action"])

    print("\nExpected Status:")
    print(result["expected_status"])

    print("\nActual Status:")
    print(result["status"])

    print("\nVerification:")
    print(result["verification_status"])

    print("\nVerified:")
    print(result["verified"])

    print("\nMessage:")
    print(result["message"])

    print("\nComplete Result:")
    print(result)