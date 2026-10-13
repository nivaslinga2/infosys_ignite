import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.agent import router as agent_router
from app.api.validate import router as validate_router
from app.api.approval import router as approval_router
from app.api.execution import router as execution_router
from app.api.audit import router as audit_router
from app.api.guardrails import router as guardrails_router

from app.middleware.rate_limit import RateLimitMiddleware

app = FastAPI(
    title="AgentShield Gateway",
    description="Agentic AI Guardrail Validator & Action Integrity Engine",
    version="1.0.0"
)

app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(agent_router)
app.include_router(validate_router)
app.include_router(approval_router)
app.include_router(execution_router)
app.include_router(audit_router)
app.include_router(guardrails_router)

@app.get("/health")
async def health_check():
    return {
        "status": "ONLINE",
        "service": "AgentShield Gateway",
        "pep_active": True,
        "action_integrity_engine": "ACTIVE"
    }

# Production Static Asset Serving for Single-Container & Cloud Deployments
possible_dist_paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist"),
    os.path.join(os.getcwd(), "frontend", "dist"),
    "/app/frontend/dist"
]

frontend_dist = next((p for p in possible_dist_paths if os.path.exists(p) and os.path.isdir(p)), None)

if frontend_dist:
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "status": "ONLINE",
            "service": "AgentShield Gateway",
            "pep_active": True,
            "message": "API Gateway is active. Build frontend with 'npm run build' to enable unified SPA serving."
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
