import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy.policy_engine import evaluate_policy


def test_low_risk_allows():
    result = evaluate_policy(
        risk_score=0.30,
        recommended_action="ALLOW"
    )

    assert result["policy_result"] == "APPROVED"


def test_medium_risk_review():
    result = evaluate_policy(
        risk_score=0.75,
        recommended_action="REVIEW_TRANSACTION"
    )

    assert result["policy_result"] == "APPROVED"


def test_high_risk_blocks():
    result = evaluate_policy(
        risk_score=0.90,
        recommended_action="BLOCK_TRANSACTION"
    )

    assert result["policy_result"] == "APPROVED"


def test_block_below_threshold_is_rejected():
    result = evaluate_policy(
        risk_score=0.80,
        recommended_action="BLOCK_TRANSACTION"
    )

    assert result["policy_result"] == "REJECTED"
