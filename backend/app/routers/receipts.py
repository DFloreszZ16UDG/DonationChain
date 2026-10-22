import hashlib

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Receipt, Role, User
from ..schemas import ReceiptOut, ReceiptVerification
from ..security import require_roles
from ..services.receipts import read_validated_upload, receipt_path

router = APIRouter(prefix="/receipts", tags=["Comprobantes"])


@router.get("/{receipt_id}", response_model=ReceiptOut)
def receipt_metadata(receipt_id: str, db: Session = Depends(get_db)):
    receipt = db.get(Receipt, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    return receipt


@router.post("/{receipt_id}/verify", response_model=ReceiptVerification)
async def verify_receipt(
    receipt_id: str,
    receipt_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    receipt = db.get(Receipt, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    data, _mime = await read_validated_upload(receipt_file)
    uploaded_hash = hashlib.sha256(data).hexdigest()
    return ReceiptVerification(
        receipt_id=receipt.id,
        expected_sha256=receipt.sha256,
        uploaded_sha256=uploaded_hash,
        matches=uploaded_hash == receipt.sha256,
    )


@router.get("/{receipt_id}/download")
def download_receipt(
    receipt_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(Role.ADMIN, Role.AUDITOR, Role.ORGANIZATION)),
):
    receipt = db.get(Receipt, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    path = receipt_path(receipt.stored_name)
    if not path.exists():
        raise HTTPException(status_code=410, detail="El archivo ya no está disponible")
    return FileResponse(path, media_type=receipt.mime_type, filename=receipt.original_name)
