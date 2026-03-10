"""Main FastAPI application for Catalog Service."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.api import router
from src.config import settings
from src.db.session import init_db
from src.middleware.logging import LoggingMiddleware

# Add shared module to path
# In Docker: /app/shared/src, in local: services/shared/src
if Path("/app/shared/src").exists():
    shared_path = Path("/app/shared/src")
else:
    shared_path = Path(__file__).parent.parent.parent / "shared" / "src"
sys.path.insert(0, str(shared_path))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.service_name,
    description="Catalog Service API for managing products",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=JSONResponse,
)

# Setup error handlers
from exceptions import setup_error_handlers

setup_error_handlers(app)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

app.include_router(router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.service_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
    )
