"""DonationChain FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import SessionLocal, create_database
from .routers import admin, audit, auth, blockchain, campaigns, receipts, transactions
from .seed import seed_development_data


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    create_database()
    settings.receipt_directory.mkdir(parents=True, exist_ok=True)
    if settings.environment == "development":
        with SessionLocal() as db:
            seed_development_data(db)
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="API para trazabilidad verificable de donaciones y gastos.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(receipts.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(blockchain.router, prefix="/api")


@app.get("/api/health", tags=["Sistema"])
def health():
    return {"status": "ok", "service": settings.app_name, "version": "1.0.0"}
