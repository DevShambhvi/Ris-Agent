from sqlalchemy import text

from .database import engine


def create_case(
    transaction_id: str,
    priority: str,
    investigation_summary: str
):
    """
    Create an investigation case for a transaction.
    """

    query = text("""
        INSERT INTO cases (
            transaction_id,
            status,
            priority,
            investigation_summary
        )
        SELECT
            id,
            'OPEN',
            :priority,
            :investigation_summary
        FROM transactions
        WHERE transaction_id = :transaction_id
        RETURNING
            id,
            transaction_id,
            status,
            priority,
            investigation_summary,
            created_at
    """)

    with engine.begin() as connection:

        result = connection.execute(
            query,
            {
                "transaction_id": transaction_id,
                "priority": priority,
                "investigation_summary": investigation_summary
            }
        ).mappings().first()

    if not result:
        raise ValueError(
            f"Transaction {transaction_id} not found."
        )

    return dict(result)


def get_case(case_id: int):
    """
    Retrieve a single investigation case.
    """

    query = text("""
        SELECT
            id,
            transaction_id,
            status,
            priority,
            assigned_to,
            investigation_summary,
            created_at,
            resolved_at
        FROM cases
        WHERE id = :case_id
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {
                "case_id": case_id
            }
        ).mappings().first()

    if not result:
        raise ValueError(
            f"Case {case_id} not found."
        )

    return dict(result)


def get_transaction_case(transaction_id: str):
    """
    Retrieve the latest case associated with a transaction.
    """

    query = text("""
        SELECT
            c.id,
            c.transaction_id,
            c.status,
            c.priority,
            c.assigned_to,
            c.investigation_summary,
            c.created_at,
            c.resolved_at
        FROM cases c
        JOIN transactions t
            ON c.transaction_id = t.id
        WHERE t.transaction_id = :transaction_id
        ORDER BY c.created_at DESC
        LIMIT 1
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {
                "transaction_id": transaction_id
            }
        ).mappings().first()

    if not result:
        return None

    return dict(result)


def resolve_case(case_id: int):
    """
    Mark an investigation case as resolved.
    """

    query = text("""
        UPDATE cases
        SET
            status = 'RESOLVED',
            resolved_at = CURRENT_TIMESTAMP
        WHERE id = :case_id
        RETURNING
            id,
            transaction_id,
            status,
            priority,
            investigation_summary,
            created_at,
            resolved_at
    """)

    with engine.begin() as connection:

        result = connection.execute(
            query,
            {
                "case_id": case_id
            }
        ).mappings().first()

    if not result:
        raise ValueError(
            f"Case {case_id} not found."
        )

    return dict(result)