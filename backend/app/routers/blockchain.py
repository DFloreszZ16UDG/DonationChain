from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import AuditLog, Role, User
from ..schemas import AuditOut, BlockchainStatus
from ..security import require_roles
from ..services.blockchain import anchor_audit_entry, network_status

router = APIRouter(prefix="/blockchain", tags=["Blockchain"])


@router.get("/status", response_model=BlockchainStatus)
def status():
    settings = get_settings()
    network = network_status()
    return BlockchainStatus(
        network="Ethereum Sepolia (Proof of Stake)",
        chain_id=settings.blockchain_chain_id,
        rpc_connected=network.connected,
        latest_block=network.latest_block,
        contract_configured=bool(settings.blockchain_contract_address),
        writes_enabled=settings.blockchain_writes_enabled,
        explorer_url=settings.blockchain_explorer_url,
        message=network.message,
    )


@router.post("/anchor/{audit_id}", response_model=AuditOut)
def anchor(
    audit_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(Role.ADMIN)),
):
    entry = db.get(AuditLog, audit_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entrada de auditoría no encontrada")
    if entry.blockchain_tx_hash:
        return entry
    try:
        return anchor_audit_entry(db, entry)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"No fue posible anclar el registro: {exc}"
        ) from exc
