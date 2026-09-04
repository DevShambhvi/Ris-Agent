from policy.rules import HIGH_RISK_THRESHOLD, BLOCK_THRESHOLD


def evaluate_policy(risk_score, recommendation):

    if recommendation not in [
        "ALLOW",
        "REVIEW_TRANSACTION",
        "BLOCK_TRANSACTION"
    ]:
        return {
            "policy_result": "REJECTED",
            "reason": "Action is not allowed by policy."
        }

    if recommendation == "BLOCK_TRANSACTION":
        if risk_score >= BLOCK_THRESHOLD:
            return {
                "policy_result": "APPROVED",
                "reason": "Risk score meets the blocking threshold."
            }

        return {
            "policy_result": "REJECTED",
            "reason": "Risk score is below the blocking threshold."
        }

    if recommendation == "REVIEW_TRANSACTION":
        if risk_score >= HIGH_RISK_THRESHOLD:
            return {
                "policy_result": "APPROVED",
                "reason": "Transaction qualifies for investigation review."
            }

        return {
            "policy_result": "REJECTED",
            "reason": "Risk score is too low for mandatory review."
        }

    return {
        "policy_result": "APPROVED",
        "reason": "Transaction is allowed by policy."
    }

if __name__ == "__main__":

    result = evaluate_policy(
        risk_score=0.95,
        recommendation="BLOCK_TRANSACTION"
    )

    print("Policy Decision:")
    print(result)