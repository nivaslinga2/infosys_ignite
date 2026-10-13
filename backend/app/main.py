from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.agent import router as agent_router
from app.api.validate import router as validate_router
from app.api.approval import router as approval_router
from app.api.execution import router as execution_router
from app.api.audit import router as audit_router
from app.api.guardrails import router as guardrails_router

from app.middleware.rate_limit import RateLimitMiddleware

app = FastAPI(
    title="AgentShield Gateway",
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


app.include_router(agent_router)
app.include_router(validate_router)
app.include_router(approval_router)
app.include_router(execution_router)
app.include_router(audit_router)
app.include_router(guardrails_router)


@app.get("/")
async def health_check():
    return {
        "status": "ONLINE",
        "service": "AgentShield Gateway",
        "pep_active": True,
        "qualcomm_npu_active": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
