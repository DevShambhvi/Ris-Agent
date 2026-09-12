RIS-Agent — AI Risk Investigation System

RIS-Agent is an AI-assisted payment risk investigation system designed to detect suspicious transactions, investigate the reasons behind the risk, make controlled decisions, execute safe actions, verify the outcome, and maintain a complete audit trail.

Overview:

Traditional payment-risk systems often focus mainly on detecting suspicious transactions.

RIS-Agent goes one step further by combining Machine Learning, RAG, AI investigation, deterministic policies, backend actions, verification, case management, and auditability into one end-to-end workflow.

Core Workflow

Transaction
     ↓
ML Risk Detection
     ↓
RAG Knowledge Retrieval
     ↓
AI Investigation Agent
     ↓
Policy Engine
     ↓
Action Execution
     ↓
Action Verification
     ↓
Case Management + Audit Trail

The system is designed around a simple principle:

AI investigates and recommends; deterministic policies authorize; the backend executes; verification confirms the result.

Architecture: 

ML — Pattern Detector

Analyzes transaction features and generates a risk score.

RAG — Reference Book

Retrieves relevant payment-risk rules and knowledge for the investigation.

AI Agent — Investigator

Combines transaction context with retrieved risk knowledge, identifies relevant evidence, and recommends an action.

Policy Engine — Safety Officer

Validates the agent's recommendation against deterministic rules and risk thresholds.

Backend — Hands

Executes the approved action and verifies the resulting transaction state.

-Key Features: 

Machine learning-based transaction risk scoring

Suspicious transaction detection

RAG-based risk knowledge retrieval

AI-assisted transaction investigation

Evidence-based risk analysis

Deterministic policy validation

Safe transaction actions

Post-action verification

Automated case creation and management

Complete audit trail

PostgreSQL persistent storage

Interactive Streamlit dashboard

Live end-to-end transaction investigation

Normal and high-risk demo scenarios

ML Model: 

The system uses a Random Forest classifier named random_forest_v1.

The model classifies transactions as:

0 → Normal
1 → Suspicious

Dataset

Total transactions:       500
Training transactions:    400
Testing transactions:     100
Original features:          8
Encoded features:          15

Model Performance

Test Accuracy: 94%

Class

Precision

Recall

F1-Score

Support

Normal

0.95

0.97

0.96

79

Suspicious

0.89

0.81

0.85

21

Overall

0.94

0.94

0.94

100

Confusion Matrix

                 Predicted
                 Normal  Suspicious

Actual Normal       77       2
Actual Suspicious    4      17

RAG Knowledge Base:

Current payment-risk rules:

RISK-001 → High Transaction Velocity
RISK-002 → Repeated Payment Failures
RISK-003 → Unusually High Transaction Amount
RISK-004 → New Account Activity
RISK-005 → Geographic Anomaly

The system distinguishes between retrieved knowledge and detected evidence. A retrieved rule is not automatically treated as confirmed evidence unless the transaction data supports that risk signal.

AI Investigation:

When a suspicious transaction is detected, the investigation agent:

Retrieves relevant risk knowledge.

Examines the transaction context.

Identifies supported risk signals.

Determines the risk level.

Recommends an appropriate action.

Passes the recommendation to the policy engine.

Example:

Transaction
    ↓
Risk Score = 0.865
    ↓
HIGH RISK
    ↓
RAG retrieves relevant rules
    ↓
Agent identifies 4 supported risk signals
    ↓
Recommendation: BLOCK_TRANSACTION

Policy Engine:

The AI agent does not directly control transaction actions.

Risk Thresholds

HIGH_RISK_THRESHOLD = 0.70
BLOCK_THRESHOLD      = 0.85

Supported Actions

ALLOW
REVIEW_TRANSACTION
BLOCK_TRANSACTION

Example:

Risk Score = 0.865

0.865 >= 0.85
        ↓
BLOCK_TRANSACTION allowed

This provides a safety layer between AI reasoning and real transaction actions.

Action Execution & Verification:

After executing an action, the system checks the resulting transaction state.

Agent Recommendation
        ↓
BLOCK_TRANSACTION
        ↓
Policy
        ↓
APPROVED
        ↓
Backend
        ↓
BLOCKED
        ↓
Verification
        ↓
VERIFIED

Example:

Expected Status: BLOCKED
Actual Status:   BLOCKED

Verification: VERIFIED

Example High-Risk Investigation:

Example suspicious transaction:

Amount:              ₹50,000
Payment Method:      CARD
Failed Attempts:     10
Account Age:         1 day
Transaction Hour:    3 AM
Transactions / 1h:   30

Example result:

Risk Score:        0.865
Risk Level:        HIGH
Detected Signals:  4
RAG Rules:         5 retrieved
Recommendation:    BLOCK_TRANSACTION
Policy:            APPROVED
Action:             BLOCKED
Verification:      VERIFIED
Case Priority:     CRITICAL
Case Status:       OPEN

Normal Transaction Scenario: 

The system can also allow normal transactions:

Normal Transaction
        ↓
ML Risk Detection
        ↓
LOW RISK
        ↓
ALLOW
        ↓
SUCCESS

Dashboard: 

The Streamlit dashboard provides:

Overview — system and risk statistics

Transactions — transaction-level risk information

Investigations — ML, RAG, agent, policy, and action results

Cases — investigation case management

Audit Trail — complete system activity history

Live Demo — create and investigate transactions in real time

Database:

RIS-Agent uses PostgreSQL for persistent storage.

Main tables:

users
transactions
risk_assessments
risk_rules
policy_decisions
cases
audit_logs

This allows transactions, risk assessments, investigations, policy decisions, cases, and actions to remain available after the live demo.

Audit Trail:

Important stages of the risk workflow are recorded for traceability:

Transaction
     ↓
Risk Assessment
     ↓
Investigation
     ↓
Policy Decision
     ↓
Action
     ↓
Action Verification

The audit trail helps answer:

Why was this transaction blocked?

Project Structure:

Ris-Agent/
│
├── agent/
│   └── investigator.py
│
├── backend/
│   └── app/
│       └── main.py
│
├── database/
│   └── schema.sql
│
├── ml/
│   ├── train_model.py
│   ├── predict.py
│   └── detector.py
│
├── policy/
│   ├── rules.py
│   └── policy_engine.py
│
├── rag/
│   ├── rag_service.py
│   ├── retriever.py
│   └── knowledge_base.py
│
├── simulator/
│   └── ...
│
├── tests/
│   └── ...
│
├── risk_transactions_500.csv
├── app.py
├── README.md
└── .env.example

⚙️ Technology Stack

Technology

Purpose

Python

Core development

FastAPI

Backend APIs

Streamlit

Interactive dashboard

PostgreSQL

Persistent database

SQLAlchemy

Database interaction

Scikit-learn

Machine Learning

Random Forest

Risk classification

RAG

Risk knowledge retrieval

ChromaDB

Vector knowledge storage

Pydantic

Data validation

Pandas

Data processing

Plotly

Dashboard visualization

Running the Project: 

1. Clone the repository

git clone https://github.com/DevShambhvi/Ris-Agent.git
cd Ris-Agent

2. Create the virtual environment

python -m venv venv

3. Activate the virtual environment

Git Bash

source venv/Scripts/activate

Windows CMD

venv\Scripts\activate

4. Install dependencies

pip install -r requirements.txt

5. Configure environment variables

Create a .env file based on:

.env.example

6. Configure PostgreSQL

Create the required PostgreSQL database and apply:

database/schema.sql

7. Start the FastAPI backend

python -m backend.app.main

8. Start the Streamlit dashboard

Open another terminal with the virtual environment activated:

streamlit run app.py

The dashboard will be available at:

http://localhost:8501

Testing:

Run the automated tests:

pytest -q

Project Objective:

The objective of RIS-Agent is to build a payment-risk system that does more than simply flag suspicious transactions.

It combines:

Detection
    +
Investigation
    +
Decision Making
    +
Safe Execution
    +
Verification
    +
Auditability

into one end-to-end workflow.

The system demonstrates how AI can assist with payment-risk investigations while keeping transaction actions bounded by deterministic policies and verified backend execution.

Future Improvements:

Larger real-world transaction datasets

More advanced behavioral and temporal features

Historical geographic anomaly detection

Model monitoring and drift detection

Additional risk rules

More configurable policy rules

Human-in-the-loop investigation workflows

Production-scale deployment

Advanced agent reasoning

Real-time payment gateway integration

Project: 

RIS-Agent — AI Risk Investigation System

Built for the Razorpay Buildathon 2026.

ML → Detect
RAG → Retrieve
Agent → Investigate
Policy → Authorize
Backend → Execute
Verification → Confirm
Audit → Explain