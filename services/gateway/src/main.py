"""Main Gateway Application"""

import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.config import settings
from src.middleware import RequestIdMiddleware, LoggingMiddleware, AuthMiddleware
from src.proxy import proxy_request

# Add shared module to path
# In Docker: /app/shared/src, in local: services/shared/src
if Path("/app/shared/src").exists():
    shared_path = Path("/app/shared/src")
else:
    shared_path = Path(__file__).parent.parent.parent / "shared" / "src"
sys.path.insert(0, str(shared_path))

# Create FastAPI app
app = FastAPI(
    title="API Gateway",
    description="Unified entry point for all SOA 2026 services",
    version="1.0.0",
)

# Setup error handlers
from exceptions import setup_error_handlers

setup_error_handlers(app)

# Add middleware
app.add_middleware(RequestIdMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gateway"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(request: Request):
    """Catch all route for proxying requests"""
    return await proxy_request(request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.GATEWAY_HOST,
        port=settings.GATEWAY_PORT,
        reload=True,
    )
