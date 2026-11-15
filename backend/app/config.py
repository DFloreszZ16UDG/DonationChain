"""Runtime configuration read from environment variables."""

import os
import secrets
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    app_name: str
    environment: str
    database_url: str
    auto_create_database: bool
    jwt_secret: str
    access_token_minutes: int
    login_rate_limit_attempts: int
    login_rate_limit_window_seconds: int
    receipt_directory: Path
    storage_backend: str
    s3_bucket: str
    s3_prefix: str
    s3_region: str
    s3_endpoint_url: str
    max_receipt_bytes: int
    cors_origins: tuple[str, ...]
    trusted_hosts: tuple[str, ...]
    force_https: bool
    blockchain_rpc_url: str
    blockchain_chain_id: int
    blockchain_contract_address: str
    blockchain_private_key: str
    blockchain_explorer_url: str

    @property
    def blockchain_writes_enabled(self) -> bool:
        return bool(
            self.blockchain_rpc_url
            and self.blockchain_contract_address
            and self.blockchain_private_key
        )


@lru_cache
def get_settings() -> Settings:
    environment = os.getenv("ENVIRONMENT", "development")
    jwt_secret = os.getenv("JWT_SECRET", "")
    if not jwt_secret:
        if environment != "development":
            raise RuntimeError("JWT_SECRET es obligatorio fuera del entorno de desarrollo")
        jwt_secret = secrets.token_urlsafe(48)
    if environment != "development" and (
        len(jwt_secret) < 32 or jwt_secret.lower().startswith("replace-with")
    ):
        raise RuntimeError("JWT_SECRET debe contener al menos 32 caracteres")
    receipt_directory = Path(
        os.getenv("RECEIPT_DIRECTORY", str(BACKEND_DIR / "storage" / "receipts"))
    ).resolve()
    origins = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    )
    trusted_hosts = tuple(
        host.strip()
        for host in os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
        if host.strip()
    )
    database_url = os.getenv(
        "DATABASE_URL", f"sqlite:///{(BACKEND_DIR / 'donationchain.db').as_posix()}"
    )
    # Several hosting providers still expose the legacy postgres:// scheme.
    if database_url.startswith("postgres://"):
        database_url = "postgresql+psycopg://" + database_url.removeprefix("postgres://")
    elif database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    if environment == "production" and database_url.startswith("sqlite"):
        raise RuntimeError("Producción requiere PostgreSQL; SQLite solo se admite en desarrollo")
    if environment == "production" and "*" in origins:
        raise RuntimeError("CORS_ORIGINS no puede usar '*' en producción")
    storage_backend = os.getenv("STORAGE_BACKEND", "local").strip().lower()
    if storage_backend not in {"local", "s3"}:
        raise RuntimeError("STORAGE_BACKEND debe ser 'local' o 's3'")
    s3_bucket = os.getenv("S3_BUCKET", "").strip()
    if storage_backend == "s3" and not s3_bucket:
        raise RuntimeError("S3_BUCKET es obligatorio cuando STORAGE_BACKEND=s3")
    s3_prefix_value = os.getenv("S3_PREFIX", "receipts").strip().strip("/")
    return Settings(
        app_name="DonationChain API",
        environment=environment,
        database_url=database_url,
        auto_create_database=os.getenv(
            "AUTO_CREATE_DATABASE", "true" if environment in {"development", "test"} else "false"
        ).lower()
        in {"1", "true", "yes"},
        jwt_secret=jwt_secret,
        access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "480")),
        login_rate_limit_attempts=int(os.getenv("LOGIN_RATE_LIMIT_ATTEMPTS", "8")),
        login_rate_limit_window_seconds=int(os.getenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "300")),
        receipt_directory=receipt_directory,
        storage_backend=storage_backend,
        s3_bucket=s3_bucket,
        s3_prefix=f"{s3_prefix_value}/" if s3_prefix_value else "",
        s3_region=os.getenv("S3_REGION", "").strip(),
        s3_endpoint_url=os.getenv("S3_ENDPOINT_URL", "").strip(),
        max_receipt_bytes=int(os.getenv("MAX_RECEIPT_BYTES", str(10 * 1024 * 1024))),
        cors_origins=origins,
        trusted_hosts=trusted_hosts,
        force_https=os.getenv("FORCE_HTTPS", "false").lower() in {"1", "true", "yes"},
        blockchain_rpc_url=os.getenv(
            "BLOCKCHAIN_RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com"
        ),
        blockchain_chain_id=int(os.getenv("BLOCKCHAIN_CHAIN_ID", "11155111")),
        blockchain_contract_address=os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS", ""),
        blockchain_private_key=os.getenv("BLOCKCHAIN_PRIVATE_KEY", ""),
        blockchain_explorer_url=os.getenv(
            "BLOCKCHAIN_EXPLORER_URL", "https://sepolia.etherscan.io"
        ),
    )
