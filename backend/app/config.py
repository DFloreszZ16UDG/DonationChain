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
    jwt_secret: str
    access_token_minutes: int
    receipt_directory: Path
    max_receipt_bytes: int
    cors_origins: tuple[str, ...]
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
    return Settings(
        app_name="DonationChain API",
        environment=environment,
        database_url=os.getenv(
            "DATABASE_URL", f"sqlite:///{(BACKEND_DIR / 'donationchain.db').as_posix()}"
        ),
        jwt_secret=jwt_secret,
        access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "480")),
        receipt_directory=receipt_directory,
        max_receipt_bytes=int(os.getenv("MAX_RECEIPT_BYTES", str(10 * 1024 * 1024))),
        cors_origins=origins,
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
