from rag.rag_service import get_relevant_knowledge
from policy.policy_engine import evaluate_policy

from backend.app.database import engine
from backend.app.actions import apply_transaction_action
from backend.app.cases import create_case, get_transaction_case
from backend.app.audit import create_audit_log

from importlib import import_module

# Load SQLAlchemy dynamically so static analysis does not require its optional type stubs in this module.
text = import_module("sqlalchemy").text

# GET TRANSACTION + LATEST RISK ASSESSMENT
def get_transaction(transaction_id):

    query = text("""
        SELECT
            t.id,
            t.transaction_id,
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

        ORDER BY r.created_at DESC

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

# AGENT RECOMMENDATION
def determine_recommendation(
    risk_score,
    evidence,
    transaction
):

    # Count extreme contextual signals
    extreme_signals = 0

    if transaction["amount"] >= 10000:
        extreme_signals += 1

    if transaction["failed_attempts"] >= 5:
        extreme_signals += 1

    if transaction["user_txn_count_1h"] >= 10:
        extreme_signals += 1

    if transaction["account_age_days"] <= 7:
        extreme_signals += 1

    # BLOCK when high ML risk is combined with
    # multiple extreme transaction signals.
    if risk_score >= 0.80 and extreme_signals >= 2:
        return "BLOCK_TRANSACTION"

    # High ML risk fallback
    if risk_score >= 0.90:
        return "BLOCK_TRANSACTION"

    # Medium/high risk → manual review
    if risk_score >= 0.70:
        return "REVIEW_TRANSACTION"

    # Otherwise allow
    return "ALLOW"

# EVALUATE RAG EVIDENCE AGAINST TRANSACTION
def evaluate_evidence(transaction, risk_rules):

    evidence = []

    rules_by_id = {
        rule["id"]: rule
        for rule in risk_rules
        if rule.get("id")
    }

    # Helper for adding evidence consistently
    def add_evidence(rule_id):

        rule = rules_by_id.get(rule_id)

        if not rule:
            return

        evidence.append({
            "id": rule["id"],
            "title": rule.get(
                "title",
                "Unknown risk rule"
            ),
            "category": rule.get(
                "category",
                "Unknown"
            ),
            "content": rule.get(
                "content",
                ""
            ),
            "severity": rule.get(
                "severity",
                "UNKNOWN"
            ),
            "recommended_action": rule.get(
                "recommended_action",
                "REVIEW_TRANSACTION"
            )
        })

    if transaction["user_txn_count_1h"] >= 5:

        add_evidence("RISK-001")

    if transaction["failed_attempts"] >= 3:

        add_evidence("RISK-002")

    if transaction["amount"] >= 3000:

        add_evidence("RISK-003")

    if transaction["account_age_days"] <= 30:

        add_evidence("RISK-004")

    return evidence

# BUILD INVESTIGATION RESULTS
def build_investigation_result(
    transaction,
    risk_score,
    evidence,
    risk_rules,
    transaction_context,
    recommendation
):

    return {

        "transaction_id": (
            transaction["transaction_id"]
        ),

        "risk_score": risk_score,

        "risk_level": (
            transaction["risk_level"]
        ),

        "model_version": (
            transaction["model_version"]
        ),

        "evidence": evidence,

        "evidence_count": len(evidence),

        "retrieved_rules": [
            {
                "id": rule["id"],
                "title": rule.get(
                    "title",
                    "Unknown rule"
                ),
                "severity": rule.get(
                    "severity",
                    "UNKNOWN"
                ),
                "similarity_distance": rule.get(
                    "similarity_distance"
                )
            }
            for rule in risk_rules
        ],

        "retrieved_rule_count": len(
            risk_rules
        ),

        "transaction_context_available": (
            transaction_context is not None
        ),

        "recommendation": recommendation,

        "investigation_status": "COMPLETED"
    }

# INVESTIGATION
def investigate(transaction_id):

    # 1. Retrieve transaction + ML assessment
    transaction = get_transaction(
        transaction_id
    )

    if not transaction:

        return {
            "success": False,
            "investigation_status": "FAILED",
            "error": (
                f"Transaction {transaction_id} not found."
            )
        }

    if transaction["risk_score"] is None:

        return {
            "success": False,
            "investigation_status": "FAILED",
            "error": (
                "No risk assessment found for transaction."
            )
        }

    risk_score = float(
        transaction["risk_score"]
    )

    # 2. RAG Query 
    rag_query = (
        f"large payment of {transaction['amount']} "
        f"with {transaction['failed_attempts']} failed "
        f"payment attempts, "
        f"{transaction['user_txn_count_1h']} transactions "
        f"within one hour, "
        f"account age {transaction['account_age_days']} days"
    )

    # 3. Retrieve semantic rules + transaction context
    try:

        rag_result = get_relevant_knowledge(
            query=rag_query,
            transaction_id=transaction_id,
            top_k=5
        )

    except Exception as error:

        return {
            "success": False,
            "investigation_status": "FAILED",
            "error": (
                "Knowledge retrieval failed."
            ),
            "details": str(error),
            "transaction_id": transaction_id
        }

    if not isinstance(rag_result, dict):

        return {
            "success": False,
            "investigation_status": "FAILED",
            "error": (
                "Invalid response from knowledge system."
            ),
            "transaction_id": transaction_id
        }

    risk_rules = rag_result.get(
        "risk_rules",
        []
    )

    transaction_context = rag_result.get(
        "transaction_context"
    )

    # 4. Evaluate evidence
    evidence = evaluate_evidence(
        transaction,
        risk_rules
    )

    # 5. Agent recommendation
    recommendation = determine_recommendation(
        risk_score,
        evidence,
        transaction
    )

    # 6. Policy evaluation
    # The AI recommends.
    # The deterministic policy engine decides.

    try:

        policy_decision = evaluate_policy(
            risk_score,
            recommendation
        )

    except Exception as error:

        return {
            "success": False,
            "investigation_status": "FAILED",
            "error": (
                "Policy evaluation failed."
            ),
            "details": str(error),
            "transaction_id": transaction_id
        }

    # 7. Build investigation result
    investigation_result = build_investigation_result(
        transaction=transaction,
        risk_score=risk_score,
        evidence=evidence,
        risk_rules=risk_rules,
        transaction_context=transaction_context,
        recommendation=recommendation
    )

    # CASE MANAGEMENT
    case = None

    if recommendation in [
        "REVIEW_TRANSACTION",
        "BLOCK_TRANSACTION"
    ]:

        existing_case = get_transaction_case(
            transaction["transaction_id"]
        )

        if existing_case:

            case = existing_case

        else:

            priority = (
                "CRITICAL"
                if recommendation == "BLOCK_TRANSACTION"
                else "HIGH"
            )

            summary = (
                f"Risk score {risk_score:.3f}. "
                f"Agent recommendation: "
                f"{recommendation}. "
                f"Detected {len(evidence)} "
                f"risk signal(s)."
            )

            case = create_case(
                transaction["transaction_id"],
                priority,
                summary
            )

    # AUDIT: INVESTIGATION COMPLETED
    if case:

        create_audit_log(
            case["id"],
            "AI_AGENT",
            "INVESTIGATION_COMPLETED",
            {
                "transaction_id": (
                    transaction["transaction_id"]
                ),

                "risk_score": risk_score,

                "risk_level": (
                    transaction["risk_level"]
                ),

                "recommendation": recommendation,

                "evidence_count": len(evidence),

                "evidence": [
                    {
                        "id": item["id"],
                        "title": item["title"]
                    }
                    for item in evidence
                ],

                "retrieved_rule_count": len(
                    risk_rules
                ),

                "retrieved_rules": [
                    rule["id"]
                    for rule in risk_rules
                ],

                "transaction_context_available": (
                    transaction_context is not None
                )
            }
        )

    # AUDIT: POLICY DECISION
    if case:

        create_audit_log(
            case["id"],
            "POLICY_ENGINE",
            "POLICY_DECISION",
            {
                # IMPORTANT:
                # This allows the investigation endpoint
                # to find this policy decision by transaction.
                "transaction_id": (
                    transaction["transaction_id"]
                ),

                "recommended_action": (
                    recommendation
                ),

                "policy_result": (
                    policy_decision[
                        "policy_result"
                    ]
                ),

                "reason": (
                    policy_decision[
                        "reason"
                    ]
                ),

                "risk_score": risk_score,

                "risk_level": (
                    transaction["risk_level"]
                ),

                "policy_version": (
                    policy_decision.get(
                        "policy_version"
                    )
                )
            }
        )

    # EXECUTE APPROVED ACTION

    action_result = None

    if (
        policy_decision.get("policy_result")
        == "APPROVED"
    ):

        try:

            action_result = apply_transaction_action(
                transaction["transaction_id"],
                recommendation
            )

        except Exception as error:

            # Action execution failed

            if case:

                create_audit_log(
                    case["id"],
                    "BACKEND",
                    "ACTION_FAILED",
                    {
                        "transaction_id": (
                            transaction[
                                "transaction_id"
                            ]
                        ),

                        "requested_action": (
                            recommendation
                        ),

                        "failure_stage": (
                            "ACTION_EXECUTION"
                        ),

                        "error": str(error)
                    }
                )

            return {
                "success": False,

                "investigation_status": (
                    "ACTION_FAILED"
                ),

                "error": (
                    "Transaction action failed."
                ),

                "investigation": (
                    investigation_result
                ),

                "policy_decision": (
                    policy_decision
                ),

                "case": case,

                "action_result": None
            }

        # Audit executed action

        if case:

            create_audit_log(
                case["id"],
                "BACKEND",
                "ACTION_EXECUTED",
                {
                    "transaction_id": (
                        transaction[
                            "transaction_id"
                        ]
                    ),

                    "action": (
                        action_result.get(
                            "action",
                            recommendation
                        )
                    ),

                    "status": (
                        action_result.get(
                            "status"
                        )
                    )
                }
            )

        # ACTION VERIFICATION
        verified = action_result.get(
            "verified",
            False
        )

        if verified:

            if case:

                create_audit_log(
                    case["id"],
                    "BACKEND",
                    "ACTION_VERIFIED",
                    {
                        "transaction_id": (
                            transaction[
                                "transaction_id"
                            ]
                        ),

                        "action": (
                            action_result.get(
                                "action"
                            )
                        ),

                        "expected_status": (
                            action_result.get(
                                "expected_status"
                            )
                        ),

                        "actual_status": (
                            action_result.get(
                                "status"
                            )
                        ),

                        "verification_status": (
                            action_result.get(
                                "verification_status"
                            )
                        )
                    }
                )

        else:

            # Verification failed
            if case:

                create_audit_log(
                    case["id"],
                    "BACKEND",
                    "ACTION_FAILED",
                    {
                        "transaction_id": (
                            transaction[
                                "transaction_id"
                            ]
                        ),

                        "action": (
                            action_result.get(
                                "action"
                            )
                        ),

                        "expected_status": (
                            action_result.get(
                                "expected_status"
                            )
                        ),

                        "actual_status": (
                            action_result.get(
                                "status"
                            )
                        ),

                        "verification_status": (
                            action_result.get(
                                "verification_status"
                            )
                        ),

                        "failure_stage": (
                            "ACTION_VERIFICATION"
                        ),

                        "reason": (
                            action_result.get(
                                "message",
                                "Action verification failed."
                            )
                        )
                    }
                )

            # Important:
            # The action technically executed, but the
            # resulting database state could not be
            # verified successfully.
        
            return {
                "success": False,

                "investigation_status": (
                    "VERIFICATION_FAILED"
                ),

                "error": (
                    "Transaction action could not "
                    "be verified."
                ),

                "investigation": (
                    investigation_result
                ),

                "policy_decision": (
                    policy_decision
                ),

                "case": case,

                "action_result": action_result
            }

    else:

        # POLICY REJECTED ACTION
        if case:

            create_audit_log(
                case["id"],
                "POLICY_ENGINE",
                "ACTION_REJECTED",
                {
                    "transaction_id": (
                        transaction[
                            "transaction_id"
                        ]
                    ),

                    "requested_action": (
                        recommendation
                    ),

                    "policy_result": (
                        policy_decision.get(
                            "policy_result"
                        )
                    ),

                    "reason": (
                        policy_decision.get(
                            "reason"
                        )
                    )
                }
            )

    # FINAL RESULT
    return {

        "success": True,

        "investigation_status": (
            "COMPLETED"
        ),

        "investigation": investigation_result,

        "policy_decision": policy_decision,

        "case": case,

        "action_result": action_result
    }


if __name__ == "__main__":

    result = investigate(
        "TXN00504"
    )

    print("\n" + "=" * 60)
    print("AI RISK INVESTIGATION")
    print("=" * 60)

    print("\nInvestigation:")
    print(result.get("investigation"))

    print("\nPolicy Decision:")
    print(result.get("policy_decision"))

    print("\nCase:")
    print(result.get("case"))

    print("\nAction:")
    print(result.get("action_result"))

    print("\nInvestigation Status:")
    print(result.get("investigation_status"))

    print("\nComplete Result:")
    print(result)