from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from pydantic import BaseModel

from .database import engine


app = FastAPI(
    title="Razorpay Risk Investigation System",
    description="AI-assisted payment risk investigation platform",
    version="0.1.0"
)


class ActionRequest(BaseModel):
    action: str


@app.get("/")
def root():
    return {
        "message": "Razorpay Risk Investigation System is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/model/health")
def model_health():
    return {
        "model": "random_forest_v1",
        "status": "ready"
    }


@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str):

    query = text("""
        SELECT
            t.transaction_id,
            t.amount,
            t.payment_method,
            t.status,
            t.country,
            t.failed_attempts,
            t.account_age_days,
            t.hour,
            t.user_txn_count_1h,
            r.risk_score,
            r.risk_level,
            r.model_version
        FROM transactions t
        LEFT JOIN risk_assessments r
            ON t.id = r.transaction_id
        WHERE t.transaction_id = :transaction_id
        ORDER BY r.created_at DESC
        LIMIT 1
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"transaction_id": transaction_id}
        ).mappings().first()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return dict(result)


def apply_transaction_action(transaction_id: str, action: str):

    allowed_actions = [
        "ALLOW",
        "REVIEW_TRANSACTION",
        "BLOCK_TRANSACTION"
    ]

    if action not in allowed_actions:
        raise ValueError("Invalid action")

    if action == "BLOCK_TRANSACTION":
        new_status = "BLOCKED"

    elif action == "REVIEW_TRANSACTION":
        new_status = "UNDER_REVIEW"

    else:
        new_status = "SUCCESS"

    query = text("""
        UPDATE transactions
        SET status = :status
        WHERE transaction_id = :transaction_id
        RETURNING transaction_id, status
    """)

    with engine.begin() as connection:
        result = connection.execute(
            query,
            {
                "status": new_status,
                "transaction_id": transaction_id
            }
        ).mappings().first()

    if not result:
        raise ValueError("Transaction not found")

    return {
        "transaction_id": result["transaction_id"],
        "action": action,
        "status": result["status"],
        "message": f"Action {action} executed successfully"
    }


@app.post("/transactions/{transaction_id}/action")
def execute_action(
    transaction_id: str,
    request: ActionRequest
):

    try:
        return apply_transaction_action(
            transaction_id,
            request.action
        )

    except ValueError as error:

        error_message = str(error)

        if error_message == "Transaction not found":
            raise HTTPException(
                status_code=404,
                detail=error_message
            )

        raise HTTPException(
            status_code=400,
            detail=error_message
        )
