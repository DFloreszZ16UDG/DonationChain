"""DonationChain FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import get_settings
from .database import SessionLocal, create_database, get_db
from .routers import admin, audit, auth, blockchain, campaigns, receipts, transactions
from .seed import seed_development_data


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    if settings.auto_create_database:
        create_database()
    if settings.storage_backend == "local":
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
if settings.trusted_hosts and "*" not in settings.trusted_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.trusted_hosts))
if settings.force_https:
    app.add_middleware(HTTPSRedirectMiddleware)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response

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


@app.get("/api/ready", tags=["Sistema"])
def readiness(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "ready",
        "database": "ok",
        "storage": settings.storage_backend,
        "blockchain_writes": settings.blockchain_writes_enabled,
    }
