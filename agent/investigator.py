from rag.rag_service import get_relevant_knowledge
from policy.policy_engine import evaluate_policy
from backend.app.database import engine
from backend.app.main import apply_transaction_action
from sqlalchemy import text

def get_transaction(transaction_id):
    """
    Fetch a transaction and its latest risk assessment from PostgreSQL.
    """

    query = text("""
        SELECT
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
        return None

    return dict(result)


def determine_recommendation(risk_score):
    """
    Determine the Agent's recommended action.

    The Policy Engine will make the final authorization decision.
    """

    if risk_score >= 0.9:
        return "BLOCK_TRANSACTION"

    if risk_score >= 0.7:
        return "REVIEW_TRANSACTION"

    return "ALLOW"

def evaluate_evidence(transaction, knowledge):
    """
    Determine which RAG rules actually apply
    to the transaction.
    """

    applicable = []

    for item in knowledge:

        rule_id = item["id"]

        if rule_id == "RISK-001":
            if transaction["user_txn_count_1h"] >= 5:
                applicable.append(item)

        elif rule_id == "RISK-002":
            if transaction["failed_attempts"] >= 3:
                applicable.append(item)

        elif rule_id == "RISK-003":
            if float(transaction["amount"]) >= 3000:
                applicable.append(item)

        elif rule_id == "RISK-004":
            # For now, treat very new accounts as higher risk.
            if transaction["account_age_days"] <= 30:
                applicable.append(item)

        elif rule_id == "RISK-005":
            # Geographic anomaly will be added later
            # when we have historical user-country data.
            pass

    return applicable


def investigate(transaction_id):
    """
    Complete investigation workflow.

    Database
        ↓
    ML Risk Assessment
        ↓
    RAG Evidence
        ↓
    Investigation Report
        ↓
    Policy Engine
    """

    print("\n" + "=" * 60)
    print("AI RISK INVESTIGATION")
    print("=" * 60)

    # 1. Fetch transaction + ML assessment
    transaction = get_transaction(transaction_id)

    if not transaction:
        print(f"\nTransaction {transaction_id} not found.")
        return None

    print("\nTransaction:")
    print(f"  ID:              {transaction['transaction_id']}")
    print(f"  Amount:          {transaction['amount']} {transaction['currency']}")
    print(f"  Payment Method:  {transaction['payment_method']}")
    print(f"  Status:          {transaction['status']}")
    print(f"  Country:         {transaction['country']}")
    print(f"  Failed Attempts: {transaction['failed_attempts']}")
    print(f"  Account Age:     {transaction['account_age_days']} days")
    print(f"  Transactions 1h: {transaction['user_txn_count_1h']}")

    # 2. Read ML risk assessment
    risk_score = float(transaction["risk_score"])

    print("\nML Risk Assessment:")
    print(f"  Risk Score:      {risk_score}")
    print(f"  Risk Level:      {transaction['risk_level']}")
    print(f"  Model Version:   {transaction['model_version']}")

    # 3. Build investigation query
    rag_query = f"""
    payment risk investigation
    transaction amount {transaction['amount']}
    failed payment attempts {transaction['failed_attempts']}
    transaction velocity {transaction['user_txn_count_1h']}
    country {transaction['country']}
    """

    # 4. Retrieve supporting evidence from RAG 
    knowledge = get_relevant_knowledge(rag_query)

    applicable_knowledge = evaluate_evidence(
    transaction,
    knowledge
    )

    print("\nRAG Evidence:")

    if applicable_knowledge:
        for item in applicable_knowledge:
            print(f"\n  [{item['id']}] {item['title']}")
            print(f"  {item['content']}")
    else:
        print("  No relevant risk knowledge found.")

    # 5. Determine Agent recommendation
    recommendation = determine_recommendation(risk_score)

    evidence_ids = [
        item["id"]
        for item in applicable_knowledge
    ]

    # 6. Create investigation report
    report = {
        "transaction_id": transaction["transaction_id"],
        "risk_score": risk_score,
        "risk_level": (
            "HIGH"
            if risk_score >= 0.7
            else "MEDIUM"
            if risk_score >= 0.3
            else "LOW"
        ),
        "evidence": evidence_ids,
        "recommendation": recommendation
    }

    print("\nInvestigation Report:")
    print(f"  Transaction:     {report['transaction_id']}")
    print(f"  Risk Score:      {report['risk_score']}")
    print(f"  Risk Level:      {report['risk_level']}")
    print(f"  Evidence:        {report['evidence']}")
    print(f"  Recommendation:  {report['recommendation']}")

    # 7. Policy Engine makes the final decision
    policy_decision = evaluate_policy(
        risk_score=risk_score,
        recommendation=recommendation
    )

    print("\nPolicy Decision:")
    print(f"  Result:          {policy_decision['policy_result']}")
    print(f"  Reason:          {policy_decision['reason']}")

    
    # 8. Execute approved action through backend
    action_result = None

    if policy_decision["policy_result"] == "APPROVED":

        action_result = apply_transaction_action(
            transaction_id,
            recommendation
        )

        print("\nBackend Action:")
        print(f"  Action:           {action_result['action']}")
        print(f"  New Status:       {action_result['status']}")
        print(f"  Message:          {action_result['message']}")

    else:

        print("\nBackend Action:")
        print("  Action not executed because policy rejected it.")

    # 9. Final system decision
    final_result = {
        "investigation": report,
        "policy_decision": policy_decision,
        "action_result": action_result
    }


if __name__ == "__main__":

    # Test with a real transaction from PostgreSQL.
    investigate("TXN00005")