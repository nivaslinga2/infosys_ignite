# AgentShield: Production Deployment Guide

This guide describes how to deploy AgentShield as a production-grade, self-contained AI Agent Security Gateway and Action Integrity Engine.

---

## Architecture Overview

AgentShield is packaged as a **unified containerized service**:
- The **FastAPI backend** serves the high-performance REST API and enforces all 10 Action Integrity checks.
- In production, FastAPI also directly serves the compiled **React/Tailwind dashboard** from `frontend/dist/`, eliminating cross-origin (CORS) complexity and requiring only **a single open port (8000)**.
- If an optional cloud AI key (`QUALCOMM_API_KEY`) or OPA policy server is not configured, the system operates seamlessly with its authoritative built-in policy and semantic fallback engine.

---

## Option 1: Docker & Docker Compose (Recommended)

### Prerequisites
- Docker Engine $\ge 20.10$
- Docker Compose $\ge 2.0$

### 1. Build and Run
```bash
# Clone the repository
git clone https://github.com/nivaslinga2/infosys_ignite.git
cd infosys_ignite

# Start the unified container
docker compose up --build -d
```

### 2. Verify
- **Web UI & Dashboard**: Open [http://localhost:8000](http://localhost:8000)
- **API Documentation**: Open [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: Open [http://localhost:8000/health](http://localhost:8000/health)

### 3. Stop
```bash
docker compose down
```

---

## Option 2: Cloud PaaS Deployment (Render / Railway / Fly.io)

### Render / Railway / Fly.io (Dockerfile-based)
Because AgentShield includes a multi-stage `Dockerfile`, any modern cloud platform can deploy it directly from GitHub:

1. **Connect Repository**: Link your GitHub repository (`nivaslinga2/infosys_ignite`) to your cloud provider.
2. **Environment Type**: Select **Docker** (it will automatically detect the root `Dockerfile`).
3. **Environment Variables**:
   - `PORT=8000` (or leave default if the platform sets `$PORT` automatically)
   - `ENVIRONMENT=production`
   - `QUALCOMM_API_KEY` (optional)
4. **Health Check Path**: `/health`
5. **Deploy**: The platform will run the multi-stage build, compile the React assets, install backend dependencies, and launch Uvicorn.

---

## Option 3: Standard Linux Server (Ubuntu / Debian VPS)

### 1. Install System Dependencies
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nodejs npm git curl
```

### 2. Setup Code & Python Virtual Environment
```bash
git clone https://github.com/nivaslinga2/infosys_ignite.git /opt/agentshield
cd /opt/agentshield

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Build Frontend
```bash
cd /opt/agentshield/frontend
npm install
npm run build
```

### 4. Create Systemd Service
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

## Option 4: Local Production Run (Python Launcher)

To run the production build locally on any OS:

```bash
# 1. Ensure dependencies are installed
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..

# 2. Start the production gateway
python start_production.py --port 8000
```

---

## Verification & Pre-Deployment Checklist

Before deploying, run the automated verification suites:

```bash
# Run all 49 security and regression tests
pytest backend/tests

# Run end-to-end verification script
python backend/verify_e2e.py
```
All 49 tests should pass with 100% success rate.
