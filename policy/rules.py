# RISK POLICY CONFIGURATIONS

# Risk thresholds
HIGH_RISK_THRESHOLD = 0.70
BLOCK_THRESHOLD = 0.85

# Allowed Actions
ALLOWED_ACTIONS = {
    "ALLOW",
    "REVIEW_TRANSACTION",
    "BLOCK_TRANSACTION"
}

# SAFETY RULES
# Minimum risk score required for investigation review.
MIN_REVIEW_RISK_SCORE = HIGH_RISK_THRESHOLD

# Minimum risk score required for automatic transaction blocking.
MIN_BLOCK_RISK_SCORE = BLOCK_THRESHOLD

# Policy Configuration
POLICY_VERSION = "policy_v1"

# Action Priority
ACTION_PRIORITY = {
    "ALLOW": 1,
    "REVIEW_TRANSACTION": 2,
    "BLOCK_TRANSACTION": 3
}
