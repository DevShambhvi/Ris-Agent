# RAZORPAY AI RISK MANAGER

AI-powered payment risk investigation and response system for detecting, investigating, and safely responding to suspicious transactions.

## Overview

Razorpay AI Risk Manager combines machine learning, retrieval-augmented generation (RAG), an AI investigation agent, a deterministic policy engine, and backend APIs into one payment-risk workflow.

The system does not simply classify a transaction as risky. It investigates **why** the transaction is risky, recommends an action, validates that action against deterministic policies, executes it, verifies the result, and records the complete audit trail.

### Core Architecture

**RAG = the agent's reference book**

**ML = its pattern detector**

**Agent = its investigator**

**Policy Engine = its safety officer**

**Backend = its hands**

---

## How It Works

```text
Transaction
     │
     ▼
ML Risk Detector
     │
     │ risk score + detected patterns
     ▼
AI Investigation Agent
     │
     ├── Transaction history
     ├── Risk rules (RAG)
     └── Evidence
     │
     ▼
Recommended Action
     │
     ▼
Policy Engine
     │
     ├── ALLOW
     ├── REVIEW_TRANSACTION
     └── BLOCK_TRANSACTION
     │
     ▼
Backend Action
     │
     ▼
Verification
     │
     ▼
Audit Log + Case
```

---

## Main Components

### 1. Transaction Simulator

Generates realistic payment activity for testing and demonstration.

The simulator can produce normal and suspicious transactions involving patterns such as:

* High transaction amount
* Multiple failed attempts
* New accounts
* High transaction velocity
* Combined suspicious behavior

The simulator can generate **10,000 payment events** for demonstration workloads.

### 2. ML Risk Detector

A Random Forest model evaluates transaction-level risk using behavioral and transaction features.

Example features include:

* Transaction amount
* Failed attempts
* Account age
* Transaction hour
* User transaction count in the last hour
* Payment method
* Country
* Device and IP information

The detector produces:

```text
Risk Score
Risk Level
Detected Patterns
Model Version
```

### 3. RAG Knowledge Base

The RAG layer provides the investigation agent with relevant risk rules and operational knowledge.

Rules include:

* Velocity anomalies
* High-value transactions
* New-account activity
* Failed-payment patterns
* Geographic anomalies

The RAG layer is used as **investigative evidence**, not as the final authority for executing financial actions.

### 4. AI Investigation Agent

The agent combines:

* Transaction data
* ML risk signals
* Retrieved risk rules
* Historical evidence

It produces:

```text
Investigation
Evidence
Risk Reasoning
Recommended Action
Investigation Status
```

### 5. Policy Engine

The policy engine is deterministic and acts as the safety boundary.

The AI agent may recommend an action, but the policy engine decides whether that action is allowed.

Supported actions:

```text
ALLOW
REVIEW_TRANSACTION
BLOCK_TRANSACTION
```

Current blocking threshold:

```text
Risk Score >= 0.85
```

### 6. Backend

FastAPI provides the system APIs for:

* Transactions
* Risk assessments
* Investigations
* Actions
* Cases
* Audit logs
* Dashboard statistics

### 7. Dashboard

The dashboard provides visibility into:

* Risk overview
* Transactions
* Investigations
* Cases
* Audit trail
* Live demonstrations

---

## Safety Model

The system follows a controlled decision pipeline:

```text
Detect
  ↓
Investigate
  ↓
Recommend
  ↓
Validate
  ↓
Execute
  ↓
Verify
  ↓
Audit
```

The AI agent does **not** directly execute financial actions.

Every action passes through the deterministic policy engine.

This provides:

* Bounded actions
* Explainability
* Verification
* Auditability
* Failure handling

---

## Example Investigation

A highly suspicious transaction may produce:

```text
Transaction:
Amount: ₹50,000
Failed Attempts: 10
Account Age: 1 day
Transactions in 1 hour: 30
Transaction Hour: 03:00

ML:
Risk Score: 0.865
Risk Level: HIGH

Investigation:
Evidence Found: 4
Rules Retrieved: 5

Agent:
Recommended Action: BLOCK_TRANSACTION

Policy:
APPROVED

Execution:
BLOCKED

Verification:
VERIFIED

Case:
CRITICAL / OPEN
```

The complete sequence is recorded in the audit trail.

---

## Technology Stack

| Layer               | Technology        |
| ------------------- | ----------------- |
| Backend             | FastAPI           |
| Database            | PostgreSQL        |
| ORM/Database Access | SQLAlchemy        |
| ML                  | Scikit-learn      |
| Model               | Random Forest     |
| RAG                 | ChromaDB          |
| AI Agent            | Python            |
| Validation          | Pydantic          |
| Dashboard           | Streamlit         |
| API Testing         | Swagger / OpenAPI |
| Version Control     | Git + GitHub      |

---

## Project Structure

```text
Ris-Agent/
│
├── agent/
│   └── investigator.py
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── actions.py
│   │   ├── audit.py
│   │   ├── cases.py
│   │   └── users.py
│   └── Requirements.txt
│
├── database/
│   └── schema.sql
│
├── dashboard/
│   └── app.py
│
├── ml/
│   ├── detector.py
│   ├── train_model.py
│   └── model/
│
├── policy/
│   ├── policy_engine.py
│   └── rules.py
│
├── rag/
│   ├── db_retriever.py
│   ├── transaction_retriever.py
│   ├── retriever.py
│   ├── services.py
│   └── vector_store.py
│
├── simulator/
│   └── simulator.py
│
├── data/
│
├── tests/
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Running the Project

### 1. Clone the repository

```bash
git clone https://github.com/DevShambhvi/Ris-Agent.git
cd Ris-Agent
```

### 2. Create the virtual environment

```bash
python -m venv venv
source venv/Scripts/activate
```

### 3. Install dependencies

```bash
pip install -r backend/Requirements.txt
```

### 4. Configure environment variables

Create a `.env` file using `.env.example` as the template.

Add the required PostgreSQL and AI configuration values.

### 5. Set up PostgreSQL

Create the project database and execute:

```text
database/schema.sql
```

### 6. Start the FastAPI backend

```bash
uvicorn backend.app.main:app --reload
```

The API will be available through the FastAPI server.

Interactive API documentation is available at:

```text
/docs
```

### 7. Start the dashboard

```bash
streamlit run dashboard/app.py
```

---

## Demonstration Flow

The intended demonstration is:

```text
10,000 simulated payment events
            ↓
Suspicious transaction detected
            ↓
ML risk score generated
            ↓
AI investigates the transaction
            ↓
Relevant risk rules retrieved
            ↓
Action recommended
            ↓
Policy validates action
            ↓
Backend executes action
            ↓
Result verified
            ↓
Case + audit trail created
```

This demonstrates an end-to-end **detect → investigate → decide → act → verify → audit** payment-risk workflow.

---

## Important Design Principle

The AI is responsible for **reasoning and investigation**.

The deterministic policy engine is responsible for **authorization**.

The backend is responsible for **execution**.

This separation prevents the AI from having unrestricted control over financial actions.

---

## Project Status

Core system implemented:

* [x] PostgreSQL database
* [x] Transaction simulator
* [x] Random Forest risk detector
* [x] RAG knowledge base
* [x] AI investigation agent
* [x] Deterministic policy engine
* [x] Transaction actions
* [x] Action verification
* [x] Case management
* [x] Audit logging
* [x] FastAPI backend
* [x] Streamlit dashboard
* [x] End-to-end investigation workflow

---

## Built For

**Razorpay Buildathon 2026**

Track 02 — AI Risk Manager
