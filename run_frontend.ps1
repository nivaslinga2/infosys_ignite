$ErrorActionPreference = "Stop"
Write-Host "Starting AgentShield Frontend on Vite dev server..." -ForegroundColor Green
Set-Location frontend
npm run dev
