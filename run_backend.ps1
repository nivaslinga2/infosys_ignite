$ErrorActionPreference = "Stop"
Write-Host "Starting AgentShield Backend on http://localhost:8000..." -ForegroundColor Cyan
$env:PYTHONPATH = "backend"
.\venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
