-- ============================================================
-- Ris-Agent Database Schema
-- PostgreSQL
-- ============================================================

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    account_created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    payment_method VARCHAR(30) NOT NULL,
    merchant_id VARCHAR(50) NOT NULL,
    transaction_timestamp TIMESTAMP NOT NULL,
    status VARCHAR(30) NOT NULL,
    country VARCHAR(10),
    device_id VARCHAR(50),
    ip_id VARCHAR(50),
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    account_age_days INTEGER,
    hour INTEGER,
    user_txn_count_1h INTEGER DEFAULT 0,
    is_suspicious BOOLEAN NOT NULL DEFAULT FALSE,
    risk_reason VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_transaction_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
);

CREATE TABLE risk_assessments (
    id BIGSERIAL PRIMARY KEY,
    transaction_id BIGINT NOT NULL,
    risk_score NUMERIC(5,4) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    detected_patterns JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_risk_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(id)
);

CREATE TABLE risk_rules (
    id BIGSERIAL PRIMARY KEY,
    rule_code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    conditions JSONB,
    recommended_action VARCHAR(50),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cases (
    id BIGSERIAL PRIMARY KEY,
    transaction_id BIGINT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    assigned_to VARCHAR(100),
    investigation_summary TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,

    CONSTRAINT fk_case_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(id)
);

CREATE TABLE policy_decisions (
    id BIGSERIAL PRIMARY KEY,
    case_id BIGINT NOT NULL,
    recommended_action VARCHAR(50) NOT NULL,
    policy_result VARCHAR(30) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_policy_case
        FOREIGN KEY (case_id)
        REFERENCES cases(id)
);

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    case_id BIGINT,
    actor VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_case
        FOREIGN KEY (case_id)
        REFERENCES cases(id)
);

-- Indexes

CREATE INDEX idx_transactions_user
    ON transactions(user_id);

CREATE INDEX idx_transactions_timestamp
    ON transactions(transaction_timestamp);

CREATE INDEX idx_transactions_suspicious
    ON transactions(is_suspicious);

CREATE INDEX idx_risk_transaction
    ON risk_assessments(transaction_id);

CREATE INDEX idx_risk_rules_category
    ON risk_rules(category);

CREATE INDEX idx_cases_status
    ON cases(status);

CREATE INDEX idx_cases_priority
    ON cases(priority);

CREATE INDEX idx_audit_case
    ON audit_logs(case_id);