from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import get_settings
from src.api import orders, promo_codes
from src.db.session import engine
from src.db.models import Base

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(
    promo_codes.router, prefix="/api/v1/promo-codes", tags=["promo-codes"]
)


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
