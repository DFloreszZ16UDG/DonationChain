"""Secure receipt storage and integrity verification."""

import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from ..config import get_settings

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


@dataclass(frozen=True)
class StoredReceipt:
    original_name: str
    stored_name: str
    mime_type: str
    size_bytes: int
    sha256: str


def _detected_mime(data: bytes) -> str | None:
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return None


async def read_validated_upload(upload: UploadFile) -> tuple[bytes, str]:
    settings = get_settings()
    data = await upload.read(settings.max_receipt_bytes + 1)
    await upload.close()
    if not data:
        raise HTTPException(status_code=400, detail="El comprobante está vacío")
    if len(data) > settings.max_receipt_bytes:
        raise HTTPException(status_code=413, detail="El comprobante supera el límite de 10 MB")
    detected = _detected_mime(data)
    if detected is None or detected not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Solo se permiten comprobantes PDF, PNG o JPEG válidos",
        )
    return data, detected


async def store_receipt(upload: UploadFile) -> StoredReceipt:
    data, mime_type = await read_validated_upload(upload)
    settings = get_settings()
    settings.receipt_directory.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ALLOWED_MIME_TYPES[mime_type]}"
    destination = (settings.receipt_directory / stored_name).resolve()
    if destination.parent != settings.receipt_directory:
        raise HTTPException(status_code=400, detail="Nombre de comprobante no válido")
    destination.write_bytes(data)
    original_name = Path(upload.filename or "comprobante").name[:255]
    return StoredReceipt(
        original_name=original_name,
        stored_name=stored_name,
        mime_type=mime_type,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )


def receipt_path(stored_name: str) -> Path:
    settings = get_settings()
    candidate = (settings.receipt_directory / stored_name).resolve()
    if candidate.parent != settings.receipt_directory:
        raise HTTPException(status_code=400, detail="Ruta de comprobante no válida")
    return candidate
