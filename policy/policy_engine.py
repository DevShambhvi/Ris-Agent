from policy.rules import (
    HIGH_RISK_THRESHOLD,
    ALLOWED_ACTIONS,
    MIN_REVIEW_RISK_SCORE,
    MIN_BLOCK_RISK_SCORE,
    POLICY_VERSION,
)

# POLICY EVALUATION 
def evaluate_policy(
    risk_score,
    recommended_action
):
    """
    This policy engine independently validates whether
    that action is permitted for the given risk score.

    Policy:

        ALLOW
            -> risk < 0.70

        REVIEW_TRANSACTION
            -> risk >= 0.70

        BLOCK_TRANSACTION
            -> risk >= 0.90

    The policy engine is deterministic and does not depend
    on the AI investigator's reasoning.
    """

    # Normalize risk score
    try:
        risk_score = float(risk_score)

    except (TypeError, ValueError):

        return {
            "policy_result": "REJECTED",
            "reason": "Invalid risk score.",
            "policy_version": POLICY_VERSION
        }

    # Normalize action
    recommended_action = str(
        recommended_action
    ).upper().strip()

    # Validate risk score
    if not 0.0 <= risk_score <= 1.0:

        return {
            "policy_result": "REJECTED",
            "reason": (
                "Risk score must be between 0.0 and 1.0."
            ),
            "policy_version": POLICY_VERSION
        }

    # Validate requested action
    if recommended_action not in ALLOWED_ACTIONS:

        return {
            "policy_result": "REJECTED",
            "reason": (
                f"Action '{recommended_action}' "
                "is not permitted by policy."
            ),
            "policy_version": POLICY_VERSION
        }

    # ALLOW
    if recommended_action == "ALLOW":

        if risk_score < HIGH_RISK_THRESHOLD:

            return {
                "policy_result": "APPROVED",
                "reason": (
                    "Risk score is below the high-risk threshold."
                ),
                "policy_version": POLICY_VERSION
            }

        return {
            "policy_result": "REJECTED",
            "reason": (
                "ALLOW action rejected because the "
                "risk score is at or above the high-risk threshold."
            ),
            "policy_version": POLICY_VERSION
        }

    # REVIEW
    if recommended_action == "REVIEW_TRANSACTION":

        if risk_score >= MIN_REVIEW_RISK_SCORE:

            return {
                "policy_result": "APPROVED",
                "reason": (
                    "Transaction qualifies for "
                    "investigation review."
                ),
                "policy_version": POLICY_VERSION
            }

        return {
            "policy_result": "REJECTED",
            "reason": (
                "Review action rejected because the "
                "risk score is below the review threshold."
            ),
            "policy_version": POLICY_VERSION
        }

    # BLOCK
    if recommended_action == "BLOCK_TRANSACTION":

        if risk_score >= MIN_BLOCK_RISK_SCORE:

            return {
                "policy_result": "APPROVED",
                "reason": (
                    "Block action approved because the "
                    "risk score meets the blocking threshold."
                ),
                "policy_version": POLICY_VERSION
            }

        return {
            "policy_result": "REJECTED",
            "reason": (
                "Block action rejected because the "
                "risk score is below the blocking threshold."
            ),
            "policy_version": POLICY_VERSION
        }

    # Defensive fallback
    return {
        "policy_result": "REJECTED",
        "reason": "No applicable policy rule.",
        "policy_version": POLICY_VERSION
    }
