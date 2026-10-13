# AgentShield: Qualcomm Autonomous AI Security Gateway

> **Core Principle:** The AI agent proposes an action. AgentShield independently validates that action. Only then can the action reach a tool.

AgentShield is a **Zero-Trust Policy Enforcement Point (PEP)** and multi-vector independent validation gateway built for autonomous AI agents. No tool with side effects can ever bypass this gateway.

---

## 🏛️ Architecture Overview

```text
USER ──► QUALCOMM AI AGENT ──► ACTION INTERCEPTOR (PEP) ──► ACTION CONTRACT
                                                                    │
           ┌──────────────────────┬──────────────────────┬──────────┴───────────┐
           ▼                      ▼                      ▼                      ▼
    AI SEMANTIC CHECK        OPA POLICY             RISK ENGINE            PROVENANCE
   (Qualcomm NPU / Cloud)   (Deterministic Rego)   (Explainable Factors)   (Taint & Injections)
           │                      │                      │                      │
           └──────────────────────┼──────────────────────┼──────────────────────┘
                                  ▼                      ▼
                            REVERSIBILITY          INTENT ALIGNMENT
                             (R1 / R2 / R3)      (Goal-Drift Detection)
                                  │                      │
                                  └──────────┬───────────┘
                                             ▼
                                      DECISION ENGINE
                                             │
                       ┌─────────────────────┼─────────────────────┐
                       ▼                     ▼                     ▼
                    🟢 ALLOW              🟡 REVIEW              🔴 BLOCK
                       │                     │                     │
                       │                     ▼                     │
                       │              HUMAN APPROVAL               │
                       │                     │                     │
                       └─────────────────────┼─────────────────────┘
                                             ▼
                                      TOOL EXECUTION
                               (Payment, DB, Email, Files)
                                             │
                                             ▼
                                     IMMUTABLE AUDIT LOG
```

---

## 🚀 Key Features

1. **Zero Direct Tool Execution**:
   - The AI agent reasons and plans using **Qualcomm AI (Snapdragon NPU / Cloud AI 100)**, but produces strictly a **Tool Proposal**.
   - It has zero direct execution paths to production tools.

2. **Standardized Action Contract**:
   - Every proposal is normalized into an immutable contract tracking `Who`, `What`, `Why`, `Which Tool`, `Which Target`, `Which Environment`, and `Provenance`.

3. **10 Independent Security Modules (AgentShield Action Integrity Engine)**:
   - **Check 1: AI Semantic Validator (Qualcomm AI)**: Identifies business meaning, sensitivity, and operational side-effects.
   - **Check 2: Custom Authorization Engine (Authoritative RBAC & OPA)**: Strict deterministic rule evaluation and role-based permissions (e.g. `refund <= ₹5,000` $\rightarrow$ ALLOW, `> ₹5,000` $\rightarrow$ REVIEW, `> ₹50,000` $\rightarrow$ BLOCK).
   - **Check 3: Safety / Risk Engine**: Transparent composite score $(0 - 100)$ factoring in sensitivity, monetary outflow, environment exposure, blast radius, and reversibility.
   - **Check 4: Reversibility Taxonomy**: Classifies actions into **R1** (Instant rollback), **R2** (Time-bounded window, e.g. 24h refund settlement), and **R3** (Irreversible destruction).
   - **Check 5: Intent Alignment Engine**: Catches subtle goal-drift (e.g. User asks *"Find refund options"*, but agent proposes executing a payment $\rightarrow$ **BLOCK**).
   - **Check 6: Provenance & Injection Gate**: Taint-tracking and origin validation for untrusted external web pages.
   - **Check 7: 🛡️ Content Safety Rail**: Neutralizes hate speech, violence/weapons, self-harm, and cyberattack commands.
   - **Check 8: 🎯 Topic Control Rail**: Enforces enterprise conversational boundaries and provides polite redirection for off-topic inquiries.
   - **Check 9: 🔏 PII Detection & Reversible Masking**: High-speed detection of SSN, Aadhaar, Credit Cards, Emails, Phones, and API Secrets with reversible session vault tokenization (`[EMAIL_1]`) and exfiltration prevention.
   - **Check 10: 🔒 Prompt Injection & Normalization Guard**: Canonical NFKC normalization, invisible character inspection (`Cf`, `Cc`, `Cs` per arXiv:2504.09559), and multi-vector jailbreak defense.

4. **Human-in-the-Loop Gate**:
   - When actions are flagged for **HUMAN REVIEW**, execution halts at the gateway. Designated supervisors (`manager_21`) can inspect the risk profile and either approve or reject the action.

5. **Complete Decision Trace & Audit Trail**:
   - Retains granular telemetry, NPU latency, rule identifiers, reviewer notes, and execution results.


---

## 🛠️ Project Structure

```text
qualcomm/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application & Gateway routing
│   │   ├── api/
│   │   │   ├── agent.py             # Agent proposals & profile catalog
│   │   │   ├── validate.py          # Action Contract validation (PEP)
│   │   │   ├── approval.py          # Human supervisor review workflow
│   │   │   ├── execution.py         # Sandboxed tool dispatcher
│   │   │   └── audit.py             # Audit trail & metric endpoints
│   │   ├── core/
│   │   │   ├── action_contract.py   # Schema normalization
│   │   │   ├── decision_engine.py   # Multi-vector coordinator
│   │   │   ├── risk_engine.py       # Composite risk calculator
│   │   │   ├── reversibility.py     # R1/R2/R3 taxonomy
│   │   │   ├── provenance.py        # Taint & injection defense
│   │   │   └── intent_alignment.py  # User authorization verification
│   │   ├── ai/
│   │   │   ├── qualcomm_client.py   # Qualcomm Cloud AI / Snapdragon NPU
│   │   │   ├── semantic_validator.py# Semantic risk classifier
│   │   │   ├── intent_parser.py     # Agent planner
│   │   │   └── explanation.py       # Natural language explanations
│   │   ├── policy/
│   │   │   ├── opa_client.py        # OPA & embedded Rego evaluator
│   │   │   └── policies/
│   │   │       ├── finance.rego     # Fiscal policies & limits
│   │   │       ├── database.rego    # SQL safety policies
│   │   │       └── general.rego     # Exfiltration & communication rules
│   │   ├── tools/
│   │   │   ├── payment.py           # Financial refund & transfer tools
│   │   │   ├── database.py          # SQL & customer lookup tools
│   │   │   ├── email.py             # Ticketing & email dispatch
│   │   │   └── files.py             # File access & data export
│   │   ├── models/                  # Pydantic schemas
│   │   └── database/                # Persistent audit database
│   ├── tests/                       # 10 Automated unit tests
│   └── verify_e2e.py                # End-to-end verification script
└── frontend/                        # React + Vite application (4 screens)
```

---

## 🏃 Getting Started

### 1. Run the Backend Server
```powershell
# In d:\workspace\qualcomm:
$env:PYTHONPATH="backend"
.\venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Run the React Frontend
```powershell
# In d:\workspace\qualcomm\frontend:
npm run dev
```

### 3. Run Automated Tests
```powershell
$env:PYTHONPATH="backend"
.\venv\Scripts\pytest -v -o asyncio_mode=auto backend/tests
```

### 4. Run End-to-End Verification Suite
```powershell
$env:PYTHONPATH="backend"
.\venv\Scripts\python backend/verify_e2e.py
```
