import time
from typing import Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Protects API endpoints against Unbounded Consumption and loop attacks (OWASP LLM10).
    Enforces a sliding window per client IP (default: 120 requests/minute).
    """
    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests_log: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next):
        # Exempt health-check endpoints and docs
        if request.url.path in ["/", "/docs", "/openapi.json", "/favicon.ico"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        if client_ip not in self.requests_log:
            self.requests_log[client_ip] = []

        # Filter out timestamps older than the sliding window
        self.requests_log[client_ip] = [
            ts for ts in self.requests_log[client_ip]
            if now - ts < self.window_seconds
        ]

        if len(self.requests_log[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": "Rate limit exceeded (OWASP LLM10: Unbounded Consumption Defense). Please throttle requests."
                }
            )

        self.requests_log[client_ip].append(now)
        return await call_next(request)
