from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from .database import engine
from .actions import apply_transaction_action
from .cases import (
    create_case,
    get_case,
    get_transaction_case,
    resolve_case
)
from .audit import get_audit_logs
from ml.detector import process_transaction
from agent.investigator import investigate


app = FastAPI(
    title="Razorpay Risk Investigation System",
    description="AI-assisted payment risk investigation platform",
    version="0.1.0"
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ActionRequest(BaseModel):
    action: str


class UserCreate(BaseModel):
    name: str
    email: str


class TransactionCreate(BaseModel):
    user_id: int
    amount: float
    currency: str = "INR"
    payment_method: str
    merchant_id: str
    country: str
    device_id: str
    ip_id: str
    failed_attempts: int = 0
    account_age_days: int
    hour: int
    user_txn_count_1h: int = 0


# ============================================================
# BASIC ROUTES
# ============================================================

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


# ============================================================
# USER MANAGEMENT
# ============================================================

@app.post("/users")
def create_user(user: UserCreate):

    check_query = text("""
        SELECT id
        FROM users
        WHERE email = :email
    """)

    with engine.connect() as connection:

        existing_user = connection.execute(
            check_query,
            {"email": user.email}
        ).scalar()

    if existing_user:

        raise HTTPException(
            status_code=409,
            detail="A user with this email already exists."
        )

    insert_query = text("""
        INSERT INTO users (
            name,
            email
        )
        VALUES (
            :name,
            :email
        )
        RETURNING
            id,
            name,
            email,
            account_created_at
    """)

    with engine.begin() as connection:

        result = connection.execute(
            insert_query,
            {
                "name": user.name,
                "email": user.email
            }
        ).mappings().first()

    return {
        "success": True,
        "user": dict(result)
    }


@app.get("/users")
def get_users():

    query = text("""
        SELECT
            id,
            name,
            email,
            account_created_at
        FROM users
        ORDER BY id
    """)

    with engine.connect() as connection:

        results = connection.execute(query).mappings().all()

    return {
        "success": True,
        "users": [
            dict(row)
            for row in results
        ]
    }


@app.get("/users/{user_id}")
def get_user(user_id: int):

    query = text("""
        SELECT
            id,
            name,
            email,
            account_created_at
        FROM users
        WHERE id = :user_id
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {"user_id": user_id}
        ).mappings().first()

    if not result:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "success": True,
        "user": dict(result)
    }


# ============================================================
# CREATE TRANSACTION
# ============================================================

@app.post("/transactions")
def create_transaction(transaction: TransactionCreate):

    # --------------------------------------------------------
    # Validate user
    # --------------------------------------------------------

    user_query = text("""
        SELECT
            id,
            name,
            email,
            account_created_at
        FROM users
        WHERE id = :user_id
    """)

    with engine.connect() as connection:

        user_result = connection.execute(
            user_query,
            {
                "user_id": transaction.user_id
            }
        ).mappings().first()

    if not user_result:

        raise HTTPException(
            status_code=404,
            detail=f"User {transaction.user_id} not found."
        )

    user_data = dict(user_result)

    # --------------------------------------------------------
    # Insert transaction
    # --------------------------------------------------------

    insert_query = text("""
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
            is_suspicious
        )
        VALUES (
            :transaction_id,
            :user_id,
            :amount,
            :currency,
            :payment_method,
            :merchant_id,
            CURRENT_TIMESTAMP,
            'SUCCESS',
            :country,
            :device_id,
            :ip_id,
            :failed_attempts,
            :account_age_days,
            :hour,
            :user_txn_count_1h,
            FALSE
        )
        RETURNING
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
            user_txn_count_1h
    """)

    with engine.begin() as connection:

        # ----------------------------------------------------
        # Generate transaction ID
        # ----------------------------------------------------

        next_id = connection.execute(
            text("""
                SELECT
                    'TXN' ||
                    LPAD(
                        (
                            COALESCE(MAX(id), 0) + 1
                        )::text,
                        5,
                        '0'
                    )
                FROM transactions
            """)
        ).scalar()

        result = connection.execute(
            insert_query,
            {
                "transaction_id": next_id,
                "user_id": transaction.user_id,
                "amount": transaction.amount,
                "currency": transaction.currency,
                "payment_method": transaction.payment_method,
                "merchant_id": transaction.merchant_id,
                "country": transaction.country,
                "device_id": transaction.device_id,
                "ip_id": transaction.ip_id,
                "failed_attempts": transaction.failed_attempts,
                "account_age_days": transaction.account_age_days,
                "hour": transaction.hour,
                "user_txn_count_1h": transaction.user_txn_count_1h
            }
        ).mappings().first()

    transaction_data = dict(result)

    # --------------------------------------------------------
    # Run ML Risk Detector
    # --------------------------------------------------------

    try:

        risk_assessment = process_transaction(
            transaction_data["transaction_id"]
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"ML risk assessment failed: {str(error)}"
        )

    # --------------------------------------------------------
    # Run AI Investigation
    # --------------------------------------------------------

    try:

        investigation_result = investigate(
            transaction_data["transaction_id"]
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"AI investigation failed: {str(error)}"
        )

    # --------------------------------------------------------
    # Extract agent pipeline results
    # --------------------------------------------------------

    investigation = investigation_result.get(
        "investigation",
        {}
    )

    policy_decision = investigation_result.get(
        "policy_decision"
    )

    case = investigation_result.get(
        "case"
    )

    action_result = investigation_result.get(
        "action_result"
    )

    # --------------------------------------------------------
    # FINAL API RESPONSE
    # --------------------------------------------------------

    return {
        "success": True,

        "transaction": transaction_data,

        "user": user_data,

        "risk_assessment": risk_assessment,

        "investigation": investigation,

        "policy_decision": policy_decision,

        "case": case,

        "action_result": action_result
    }


# ============================================================
# GET TRANSACTION
# ============================================================

@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str):

    query = text("""
        SELECT
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
            r.model_version,
            r.detected_patterns

        FROM transactions t

        LEFT JOIN LATERAL (
            SELECT
                risk_score,
                risk_level,
                model_version,
                detected_patterns
            FROM risk_assessments
            WHERE risk_assessments.transaction_id = t.id
            ORDER BY created_at DESC
            LIMIT 1
        ) r ON TRUE

        WHERE t.transaction_id = :transaction_id
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {
                "transaction_id": transaction_id
            }
        ).mappings().first()

    if not result:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return {
        "success": True,
        "transaction": dict(result)
    }


# ============================================================
# GET TRANSACTION INVESTIGATION
# ============================================================

@app.get("/transactions/{transaction_id}/investigation")
def get_transaction_investigation(transaction_id: str):

    # --------------------------------------------------------
    # Get transaction + latest ML risk assessment
    # --------------------------------------------------------

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
            r.model_version,
            r.detected_patterns

        FROM transactions t

        LEFT JOIN LATERAL (
            SELECT
                risk_score,
                risk_level,
                model_version,
                detected_patterns
            FROM risk_assessments
            WHERE risk_assessments.transaction_id = t.id
            ORDER BY created_at DESC
            LIMIT 1
        ) r ON TRUE

        WHERE t.transaction_id = :transaction_id
    """)

    with engine.connect() as connection:

        transaction_result = connection.execute(
            transaction_query,
            {
                "transaction_id": transaction_id
            }
        ).mappings().first()

    if not transaction_result:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    transaction_data = dict(transaction_result)

    # --------------------------------------------------------
    # Get latest AI investigation audit event
    # --------------------------------------------------------

    investigation_query = text("""
        SELECT
            action,
            details,
            created_at
        FROM audit_logs
        WHERE action = 'INVESTIGATION_COMPLETED'
          AND details ->> 'transaction_id' = :transaction_id
        ORDER BY created_at DESC
        LIMIT 1
    """)

    # --------------------------------------------------------
    # Get latest policy decision
    # --------------------------------------------------------

    policy_query = text("""
        SELECT
            action,
            details,
            created_at
        FROM audit_logs
        WHERE action = 'POLICY_DECISION'
          AND details ->> 'transaction_id' = :transaction_id
        ORDER BY created_at DESC
        LIMIT 1
    """)

    # --------------------------------------------------------
    # Get latest backend action
    # --------------------------------------------------------

    action_query = text("""
        SELECT
            action,
            details,
            created_at
        FROM audit_logs
        WHERE action IN (
            'ACTION_EXECUTED',
            'ACTION_VERIFIED',
            'ACTION_REJECTED'
        )
        AND details ->> 'transaction_id' = :transaction_id
        ORDER BY created_at DESC
        LIMIT 1
    """)

    with engine.connect() as connection:

        investigation_result = connection.execute(
            investigation_query,
            {
                "transaction_id": transaction_id
            }
        ).mappings().first()

        policy_result = connection.execute(
            policy_query,
            {
                "transaction_id": transaction_id
            }
        ).mappings().first()

        action_result = connection.execute(
            action_query,
            {
                "transaction_id": transaction_id
            }
        ).mappings().first()

    # --------------------------------------------------------
    # Build investigation response
    # --------------------------------------------------------

    investigation = {}

    if investigation_result:

        investigation = dict(
            investigation_result["details"]
        )

        investigation["investigated_at"] = (
            investigation_result["created_at"]
        )

    policy_decision = None

    if policy_result:

        policy_decision = dict(
            policy_result["details"]
        )

        policy_decision["created_at"] = (
            policy_result["created_at"]
        )

    executed_action = None

    if action_result:

        executed_action = dict(
            action_result["details"]
        )

        executed_action["audit_action"] = (
            action_result["action"]
        )

        executed_action["created_at"] = (
            action_result["created_at"]
        )

    # --------------------------------------------------------
    # Get case
    # --------------------------------------------------------

    case = get_transaction_case(
        transaction_id
    )

    # --------------------------------------------------------
    # Return complete investigation state
    # --------------------------------------------------------

    return {
        "success": True,
        "transaction": transaction_data,
        "investigation": investigation,
        "policy_decision": policy_decision,
        "action_result": executed_action,
        "case": case
    }


# ============================================================
# EXECUTE TRANSACTION ACTION
# ============================================================

@app.post("/transactions/{transaction_id}/action")
def execute_action(
    transaction_id: str,
    request: ActionRequest
):

    try:

        result = apply_transaction_action(
            transaction_id,
            request.action
        )

        return {
            "success": True,
            **result
        }

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


# ============================================================
# CASE MANAGEMENT
# ============================================================

@app.get("/cases/{case_id}")
def get_case_endpoint(case_id: int):

    try:

        case = get_case(case_id)

        return {
            "success": True,
            "case": case
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )


@app.get("/transactions/{transaction_id}/case")
def get_transaction_case_endpoint(
    transaction_id: str
):

    case = get_transaction_case(
        transaction_id
    )

    if not case:

        raise HTTPException(
            status_code=404,
            detail="No case found for this transaction."
        )

    return {
        "success": True,
        "case": case
    }


@app.post("/cases/{case_id}/resolve")
def resolve_case_endpoint(case_id: int):

    try:

        case = resolve_case(case_id)

        return {
            "success": True,
            "case": case
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )


# ============================================================
# AUDIT TRAIL
# ============================================================

@app.get("/cases/{case_id}/audit")
def get_case_audit(case_id: int):

    try:

        get_case(case_id)

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    logs = get_audit_logs(case_id)

    return {
        "success": True,
        "case_id": case_id,
        "audit_logs": logs
    }


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@app.get("/dashboard/summary")
def dashboard_summary():

    query = text("""
        SELECT

            COUNT(*) AS total_transactions,

            COUNT(*) FILTER (
                WHERE status = 'SUCCESS'
            ) AS successful_transactions,

            COUNT(*) FILTER (
                WHERE status = 'UNDER_REVIEW'
            ) AS under_review_transactions,

            COUNT(*) FILTER (
                WHERE status = 'BLOCKED'
            ) AS blocked_transactions,

            COUNT(*) FILTER (
                WHERE is_suspicious = TRUE
            ) AS suspicious_transactions

        FROM transactions
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query
        ).mappings().first()

    return {
        "success": True,
        "summary": dict(result)
    }


# ============================================================
# RISK DISTRIBUTION
# ============================================================

@app.get("/dashboard/risk-distribution")
def risk_distribution():

    query = text("""
        SELECT
            risk_level,
            COUNT(*) AS count
        FROM risk_assessments
        GROUP BY risk_level
        ORDER BY risk_level
    """)

    with engine.connect() as connection:

        results = connection.execute(
            query
        ).mappings().all()

    return {
        "success": True,
        "risk_distribution": [
            dict(row)
            for row in results
        ]
    }


# ============================================================
# RECENT RISK EVENTS
# ============================================================

@app.get("/dashboard/recent-risk")
def recent_risk():

    query = text("""
        SELECT
            t.transaction_id,
            t.user_id,
            t.amount,
            t.currency,
            t.payment_method,
            t.country,
            t.status,
            r.risk_score,
            r.risk_level,
            r.model_version,
            r.created_at
        FROM transactions t

        JOIN LATERAL (
            SELECT
                risk_score,
                risk_level,
                model_version,
                created_at
            FROM risk_assessments
            WHERE risk_assessments.transaction_id = t.id
            ORDER BY created_at DESC
            LIMIT 1
        ) r ON TRUE

        ORDER BY r.created_at DESC
        LIMIT 10
    """)

    with engine.connect() as connection:

        results = connection.execute(
            query
        ).mappings().all()

    return {
        "success": True,
        "recent_risk": [
            dict(row)
            for row in results
        ]
    }


# ============================================================
# DASHBOARD CASES
# ============================================================

@app.get("/dashboard/cases")
def dashboard_cases():

    query = text("""
        SELECT
            c.id,
            c.transaction_id,
            t.transaction_id AS transaction_code,
            c.status,
            c.priority,
            c.assigned_to,
            c.investigation_summary,
            c.created_at,
            c.resolved_at
        FROM cases c
        JOIN transactions t
            ON c.transaction_id = t.id
        ORDER BY c.created_at DESC
    """)

    with engine.connect() as connection:

        results = connection.execute(
            query
        ).mappings().all()

    return {
        "success": True,
        "cases": [
            dict(row)
            for row in results
        ]
    }


# ============================================================
# DASHBOARD STATISTICS
# ============================================================

@app.get("/dashboard/statistics")
def dashboard_statistics():

    query = text("""
        SELECT

            COUNT(*) AS total_transactions,

            COUNT(*) FILTER (
                WHERE is_suspicious = TRUE
            ) AS suspicious_transactions,

            COUNT(*) FILTER (
                WHERE status = 'BLOCKED'
            ) AS blocked_transactions,

            COUNT(*) FILTER (
                WHERE status = 'UNDER_REVIEW'
            ) AS review_transactions,

            COALESCE(
                SUM(amount),
                0
            ) AS total_value,

            COALESCE(
                SUM(amount) FILTER (
                    WHERE status = 'BLOCKED'
                ),
                0
            ) AS blocked_value

        FROM transactions
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query
        ).mappings().first()

    return {
        "success": True,
        "statistics": dict(result)
    }


# ============================================================
# DASHBOARD AUDIT
# ============================================================

@app.get("/dashboard/audit")
def dashboard_audit():

    query = text("""
        SELECT
            a.id,
            a.case_id,
            a.actor,
            a.action,
            a.details,
            a.created_at
        FROM audit_logs a
        ORDER BY a.created_at DESC
        LIMIT 100
    """)

    with engine.connect() as connection:

        results = connection.execute(
            query
        ).mappings().all()

    return {
        "success": True,
        "audit_logs": [
            dict(row)
            for row in results
        ]
    }


# ============================================================
# DASHBOARD TRANSACTIONS
# ============================================================

@app.get("/dashboard/transactions")
def dashboard_transactions():

    query = text("""
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
            t.is_suspicious,

            u.name AS user_name,
            u.email AS user_email,

            r.risk_score,
            r.risk_level,
            r.model_version,
            r.detected_patterns

        FROM transactions t

        LEFT JOIN users u
            ON t.user_id = u.id

        LEFT JOIN LATERAL (
            SELECT
                risk_score,
                risk_level,
                model_version,
                detected_patterns
            FROM risk_assessments
            WHERE risk_assessments.transaction_id = t.id
            ORDER BY created_at DESC
            LIMIT 1
        ) r ON TRUE

        ORDER BY t.transaction_timestamp DESC
    """)

    with engine.connect() as connection:

        results = connection.execute(
            query
        ).mappings().all()

    return {
        "success": True,
        "transactions": [
            dict(row)
            for row in results
        ]
    }