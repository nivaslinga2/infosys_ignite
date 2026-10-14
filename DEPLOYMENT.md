# AgentShield: Production Deployment & Verification Guide

This guide describes how to configure, verify, deploy, and monitor AgentShield as a production-grade, self-contained AI Agent Security Gateway and Action Integrity Engine with optional Qualcomm Cloud AI 100 acceleration.

---

## Architecture Overview

AgentShield is packaged as a **unified containerized service**:
- **FastAPI Backend**: Serves the high-performance REST API and enforces all 10 Action Integrity checks (Prompt Injection Defense, PII Masking, Topic Control, RBAC, OPA, Semantic Drift, Transfer Limits, Execution Sandboxing, State Immutability, Tamper-Evident Auditing).
- **React/Tailwind Dashboard**: In production, FastAPI directly serves the compiled single-page application from `frontend/dist/`. This eliminates cross-origin (CORS) complexity and exposes the entire platform through **a single open port (8000)**.
- **Dual-Engine Inference**:
  - **Qualcomm Cloud AI 100 / Snapdragon Engine**: Uses Cirrascale Cloud AI 100 inference (`Llama-3.1-8B`) for deep semantic intent classification, argument extraction, and drift analysis.
  - **Authoritative Deterministic Fallback**: If cloud AI keys are omitted or endpoints become unreachable, AgentShield immediately falls back to its deterministic regex/AST/OPA engine with sub-millisecond latency and 0% failure rate.

---

## Environment Configuration

Create a `.env` file in the project root based on `.env.example`:

```bash
cp .env.example .env
```

### Configuration Parameters

| Variable | Description | Default / Example | Required |
| :--- | :--- | :--- | :--- |
| `PORT` | HTTP port for the unified server | `8000` | Yes |
| `ENVIRONMENT` | Runtime environment (`production` / `development`) | `production` | Yes |
| `INFERENCE_CLOUD_API_KEY` | Cirrascale Cloud AI 100 API Key | `your_api_key_here` | Optional |
| `QUALCOMM_API_KEY` | Qualcomm AI Suite Token | `your_qualcomm_token` | Optional |
| `INFERENCE_CLOUD_ENDPOINT`| Cirrascale AI Suite API Base URL | `https://aisuite.cirrascale.com/apis/v2` | Optional |
| `QUALCOMM_MODEL` | AI 100 Target Model | `Llama-3.1-8B` | Optional |
| `OPA_URL` | Open Policy Agent endpoint | `http://localhost:8181` | Optional |

> [!NOTE]
> All credentials should stay strictly in your local `.env` file or environment secrets. `.env` is gitignored to prevent accidental credential leakage.

---

## Deployment Options

### Option 1: Local / On-Premise Production Run (Python Launcher)

To run the unified production build locally on any OS (Linux, macOS, Windows):

```bash
# 1. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..

# 2. Launch production gateway
python start_production.py --port 8000 --host 0.0.0.0
```

The launcher will automatically:
1. Verify that the production React bundle exists in `frontend/dist/` (or compile it via `npm run build` if missing).
2. Start Uvicorn running `app.main:app` with production settings.
3. Serve the interactive dashboard at `http://localhost:8000/`.
4. Expose the API endpoints under `/api`, OpenAPI documentation at `/docs`, and health status at `/health`.

---

### Option 2: Docker & Docker Compose (Recommended for Containerized Environments)

#### Prerequisites
- Docker Engine $\ge 20.10$
- Docker Compose $\ge 2.0$

#### 1. Build and Run
```bash
# Build multi-stage image (frontend build + python backend) and launch in detached mode
docker compose up --build -d
```

#### 2. Verify Container Health
```bash
docker compose ps
curl http://localhost:8000/health
```

#### 3. View Logs & Stop
```bash
docker compose logs -f
docker compose down
```

---

### Option 3: Cloud PaaS Deployment (Render / Railway / Fly.io / AWS App Runner)

Because AgentShield includes an optimized multi-stage `Dockerfile`, modern PaaS platforms build and deploy directly from GitHub:

1. **Connect Repository**: Link your GitHub repository (`nivaslinga2/infosys_ignite`).
2. **Runtime / Build Pack**: Select **Docker**.
3. **Environment Variables**:
   - `PORT=8000` (or leave default if the platform sets `$PORT` dynamically)
   - `ENVIRONMENT=production`
   - `INFERENCE_CLOUD_API_KEY` / `QUALCOMM_API_KEY` (if utilizing Qualcomm Cloud AI 100)
4. **Health Check Path**: `/health`
5. **Deploy**: The platform executes the multi-stage build: compiles React into `/app/frontend/dist`, installs backend requirements into a minimal Python 3.11 slim image, and boots Uvicorn.

---

### Option 4: Production Linux Server (Ubuntu / Debian VPS with Systemd)

#### 1. Install System Dependencies
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nodejs npm git curl
```

#### 2. Setup Code & Virtual Environment
```bash
git clone https://github.com/nivaslinga2/infosys_ignite.git /opt/agentshield
cd /opt/agentshield

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Compile Frontend
```bash
cd /opt/agentshield/frontend
npm install
npm run build
cd /opt/agentshield
```

#### 4. Configure Systemd Service
Create `/etc/systemd/system/agentshield.service`:
```ini
[Unit]
Description=AgentShield AI Security Gateway
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/agentshield/backend
ExecStart=/opt/agentshield/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=3
EnvironmentFile=/opt/agentshield/.env
Environment=PORT=8000
Environment=ENVIRONMENT=production

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable agentshield
sudo systemctl start agentshield
```

---

## Verification & Pre-Deployment Checklist

AgentShield includes 5 dedicated automated test and verification suites to validate enforcement before cutting over production traffic.

### 1. Full Regression Test Suite (49 Automated Pytest Tests)
Runs complete unit, acceptance, adversarial evasion, and guardrail validation tests:
```bash
pytest backend/tests
```
*Expected Outcome: 49 passed (100% pass rate).*

---

### 2. Core 3-Case Verification Script
Tests the 3 foundational policy and human-in-the-loop flows:
```bash
python backend/prove_cases.py
```
*Evaluates:*
- **Test A (Safe Action)**: Support ticket query $\rightarrow$ Decision `ALLOW`, Mock tool execution succeeds.
- **Test B (Sensitive Action)**: ₹45,000 refund exceeding limit $\rightarrow$ Decision `HUMAN_REVIEW`, Blocked until valid supervisor approval token is submitted.
- **Test C (Prohibited Action)**: Destructive SQL deletion `DROP TABLE customers` $\rightarrow$ Decision `BLOCK`, 0 side effects in execution environment.

---

### 3. Industry 100-Case Guardrail Benchmark
Runs our comprehensive evaluation dataset against all 10 integrity layers and Qualcomm Cloud AI:
```bash
python backend/benchmark/run_evaluation.py
```
*Target & Benchmark Metrics:*
| Metric | Benchmark Result | Target Standard |
| :--- | :--- | :--- |
| Attack Detection Recall | **100.0%** | $\ge 95\%$ |
| False Positive Rate on Benign Cases | **0.0%** | $\le 1\%$ |
| Blocked-Action Execution Rate | **0.0%** | $0.0\%$ (Strict Zero Tolerance) |
| Human Review Enforcement Rate | **100.0%** | $100\%$ |
| Average Decision Latency | **0.42 ms** | $< 250$ ms |

---

### 4. Qualcomm Cloud AI 100 Live Connectivity Probe
Tests live network connectivity, API key validity, latency, and response generation on Qualcomm Cloud AI 100:
```bash
python backend/probe_qualcomm_env.py
```
*Output validates:* HTTP 200 response, Cloud AI 100 cluster responsiveness, token generation, and latency metrics.

---

### 5. Cyberattack & Evasion Defense Regression Test
Verifies that direct/indirect prompt injections and cyberattack prompts (such as firewall penetration requests) are blocked immediately and cannot trigger unauthorized lookup tools:
```bash
python backend/test_hack_prompt.py
```
*Expected Outcome: Decision `BLOCK` with `blocked_cyberattack` intent and `tool="none"`.*

---

## Monitoring & Health Endpoints

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/health` | `GET` | Service readiness probe (returns status, version, and component health) |
| `/docs` | `GET` | Interactive Swagger UI API documentation |
| `/redoc` | `GET` | ReDoc API specification |
| `/api/audit/logs` | `GET` | Retrieve append-only cryptographic audit logs for compliance |
| `/api/guardrails/rules` | `GET` | Active security policy and limit configuration |
