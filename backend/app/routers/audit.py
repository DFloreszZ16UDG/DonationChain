from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog, Donation, Expense, ExpenseStatus, Receipt, Role, User
from ..schemas import AuditOut, AuditVerification, TimelineEvent
from ..security import require_roles
from ..services.audit import verify_audit_chain

router = APIRouter(tags=["Auditoría y trazabilidad"])


@router.get("/campaigns/{campaign_id}/timeline", response_model=list[TimelineEvent])
def campaign_timeline(campaign_id: str, db: Session = Depends(get_db)):
    events: list[TimelineEvent] = []
    donations = db.scalars(select(Donation).where(Donation.campaign_id == campaign_id)).all()
    for donation in donations:
        receipt = db.get(Receipt, donation.receipt_id) if donation.receipt_id else None
        events.append(
            TimelineEvent(
                id=donation.id,
                event_type="DONATION",
                title="Donación recibida",
                description="Aportación registrada; la identidad del donante se mantiene privada",
                amount=donation.amount,
                status="REGISTRADA",
                receipt_id=donation.receipt_id,
                receipt_hash=receipt.sha256 if receipt else None,
                created_at=donation.created_at,
            )
        )
    expenses = db.scalars(
        select(Expense).where(
            Expense.campaign_id == campaign_id,
            Expense.status == ExpenseStatus.APPROVED,
        )
    ).all()
    for expense in expenses:
        receipt = db.get(Receipt, expense.receipt_id)
        events.append(
            TimelineEvent(
                id=expense.id,
                event_type="EXPENSE",
                title=expense.concept,
                description=expense.description,
                amount=expense.amount,
                status=expense.status.value,
                receipt_id=expense.receipt_id,
                receipt_hash=receipt.sha256 if receipt else None,
                created_at=expense.created_at,
            )
        )
    return sorted(events, key=lambda item: item.created_at, reverse=True)


@router.get("/audit", response_model=list[AuditOut])
def audit_entries(
    entity_type: str | None = Query(default=None, max_length=80),
    entity_id: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(Role.ADMIN, Role.AUDITOR)),
):
    query = select(AuditLog)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type.upper())
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
    return list(db.scalars(query.order_by(AuditLog.created_at.desc()).limit(limit)))


@router.get("/audit/verify", response_model=AuditVerification)
def verify_audit(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(Role.ADMIN, Role.AUDITOR)),
):
    valid, message = verify_audit_chain(db)
    return AuditVerification(valid=valid, message=message)


@router.get("/audit/{audit_id}", response_model=AuditOut)
def audit_entry(
    audit_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(Role.ADMIN, Role.AUDITOR)),
):
    entry = db.get(AuditLog, audit_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entrada de auditoría no encontrada")
    return entry
