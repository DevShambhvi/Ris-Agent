import json

from sqlalchemy import text

from .database import engine


def create_audit_log(
    case_id: int,
    actor: str,
    action: str,
    details: dict
):
    """
    Create an audit log entry for an investigation case.
    """

    query = text("""
        INSERT INTO audit_logs (
            case_id,
            actor,
            action,
            details
        )
        VALUES (
            :case_id,
            :actor,
            :action,
            CAST(:details AS jsonb)
        )
        RETURNING id
    """)

    with engine.begin() as connection:

        result = connection.execute(
            query,
            {
                "case_id": case_id,
                "actor": actor,
                "action": action,
                "details": json.dumps(details)
            }
        ).scalar()

    if not result:
        raise ValueError("Failed to create audit log.")

    return {
        "audit_log_id": result,
        "case_id": case_id,
        "actor": actor,
        "action": action
    }


def get_audit_logs(case_id: int):
    """
    Retrieve the audit trail for a case.
    """

    query = text("""
        SELECT
            id,
            case_id,
            actor,
            action,
            details,
            created_at
        FROM audit_logs
        WHERE case_id = :case_id
        ORDER BY created_at ASC
    """)

    with engine.connect() as connection:

        results = connection.execute(
            query,
            {
                "case_id": case_id
            }
        ).mappings().all()

    return [dict(row) for row in results]