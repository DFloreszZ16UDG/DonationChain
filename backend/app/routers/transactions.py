from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Allocation,
    AuditLog,
    Campaign,
    CampaignStatus,
    Donation,
    Expense,
    ExpenseStatus,
    Receipt,
    Role,
    User,
    utc_now,
)
from ..money import parse_money
from ..schemas import (
    AllocationCreate,
    AllocationOut,
    DonationAllocationTrace,
    DonationOut,
    DonationTrace,
    ExpenseOut,
    ExpenseReview,
)
from ..security import get_current_user, require_roles
from ..services.audit import record_audit
from ..services.donation_acknowledgement import build_donation_acknowledgement
from ..services.receipts import store_receipt

router = APIRouter(tags=["Donaciones y gastos"])


def _campaign_or_404(db: Session, campaign_id: str) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    return campaign


def _ensure_active(campaign: Campaign) -> None:
    if campaign.status != CampaignStatus.ACTIVE:
        raise HTTPException(status_code=409, detail="La campaña no está activa")


def _can_view_donation(user: User, donation: Donation, campaign: Campaign) -> bool:
    return (
        user.id == donation.donor_id
        or user.role in (Role.ADMIN, Role.AUDITOR)
        or (user.role == Role.ORGANIZATION and user.organization_id == campaign.organization_id)
    )


def _create_receipt_model(db: Session, upload: UploadFile, stored, user: User) -> Receipt:
    receipt = Receipt(
        original_name=stored.original_name,
        stored_name=stored.stored_name,
        mime_type=stored.mime_type,
        size_bytes=stored.size_bytes,
        sha256=stored.sha256,
        uploaded_by_id=user.id,
    )
    db.add(receipt)
    db.flush()
    return receipt


@router.get("/campaigns/{campaign_id}/donations", response_model=list[DonationOut])
def list_donations(
    campaign_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUDITOR, Role.ORGANIZATION)),
):
    campaign = _campaign_or_404(db, campaign_id)
    if user.role == Role.ORGANIZATION and campaign.organization_id != user.organization_id:
        raise HTTPException(status_code=403, detail="La campaña pertenece a otra organización")
    return list(
        db.scalars(
            select(Donation)
            .where(Donation.campaign_id == campaign_id)
            .order_by(Donation.created_at.desc())
        )
    )


@router.get("/me/donations", response_model=list[DonationOut])
def my_donations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return list(
        db.scalars(
            select(Donation)
            .where(Donation.donor_id == user.id)
            .order_by(Donation.created_at.desc())
        )
    )


@router.get("/donations/{donation_id}/trace", response_model=DonationTrace)
def donation_trace(
    donation_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    donation = db.get(Donation, donation_id)
    if donation is None:
        raise HTTPException(status_code=404, detail="Donación no encontrada")
    campaign = _campaign_or_404(db, donation.campaign_id)
    if not _can_view_donation(user, donation, campaign):
        raise HTTPException(status_code=403, detail="No puedes consultar esta donación")
    audit = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "DONATION",
            AuditLog.entity_id == donation.id,
            AuditLog.action == "DONATION_RECORDED",
        )
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )
    allocations = db.scalars(
        select(Allocation)
        .where(Allocation.donation_id == donation.id)
        .order_by(Allocation.created_at)
    ).all()
    traces: list[DonationAllocationTrace] = []
    allocated = Decimal("0.00")
    for allocation in allocations:
        expense = allocation.expense
        allocated += allocation.amount
        traces.append(
            DonationAllocationTrace(
                allocation_id=allocation.id,
                expense_id=expense.id,
                concept=expense.concept,
                description=expense.description,
                amount=allocation.amount,
                status=expense.status,
                created_at=allocation.created_at,
            )
        )
    return DonationTrace(
        donation=donation,
        campaign_name=campaign.name,
        allocated=allocated,
        unallocated=donation.amount - allocated,
        audit_id=audit.id if audit else None,
        audit_hash=audit.entry_hash if audit else None,
        anchor_status=audit.anchor_status if audit else None,
        blockchain_tx_hash=audit.blockchain_tx_hash if audit else None,
        blockchain_block_number=audit.blockchain_block_number if audit else None,
        allocations=traces,
    )


@router.get("/donations/{donation_id}/acknowledgement.pdf")
def donation_acknowledgement(
    donation_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    donation = db.get(Donation, donation_id)
    if donation is None:
        raise HTTPException(status_code=404, detail="Donación no encontrada")
    campaign = _campaign_or_404(db, donation.campaign_id)
    if not _can_view_donation(user, donation, campaign):
        raise HTTPException(status_code=403, detail="No puedes descargar este comprobante")
    audit = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "DONATION",
            AuditLog.entity_id == donation.id,
            AuditLog.action == "DONATION_RECORDED",
        )
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )
    pdf = build_donation_acknowledgement(
        donation,
        campaign,
        campaign.organization,
        audit,
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="donationchain-{donation.id}.pdf"'
            )
        },
    )


@router.post("/campaigns/{campaign_id}/donations", response_model=DonationOut, status_code=201)
async def create_donation(
    campaign_id: str,
    amount: str = Form(...),
    donor_name: str = Form(..., min_length=2, max_length=160),
    receipt_file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    campaign = _campaign_or_404(db, campaign_id)
    _ensure_active(campaign)
    exact_amount = parse_money(amount)
    receipt = None
    if receipt_file is not None:
        stored = await store_receipt(receipt_file)
        receipt = _create_receipt_model(db, receipt_file, stored, user)
    donation = Donation(
        campaign_id=campaign.id,
        donor_id=user.id,
        donor_name=donor_name.strip(),
        amount=exact_amount,
        receipt_id=receipt.id if receipt else None,
    )
    db.add(donation)
    db.flush()
    record_audit(
        db,
        user,
        "DONATION_RECORDED",
        "DONATION",
        donation.id,
        {
            "campaign_id": campaign.id,
            "amount": exact_amount,
            "receipt_hash": receipt.sha256 if receipt else None,
        },
    )
    db.commit()
    db.refresh(donation)
    return donation


@router.get("/campaigns/{campaign_id}/expenses", response_model=list[ExpenseOut])
def list_expenses(
    campaign_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUDITOR, Role.ORGANIZATION)),
):
    campaign = _campaign_or_404(db, campaign_id)
    if user.role == Role.ORGANIZATION and campaign.organization_id != user.organization_id:
        raise HTTPException(status_code=403, detail="La campaña pertenece a otra organización")
    return list(
        db.scalars(
            select(Expense)
            .where(Expense.campaign_id == campaign_id)
            .order_by(Expense.created_at.desc())
        )
    )


@router.post("/campaigns/{campaign_id}/expenses", response_model=ExpenseOut, status_code=201)
async def create_expense(
    campaign_id: str,
    amount: str = Form(...),
    concept: str = Form(..., min_length=2, max_length=240),
    description: str = Form(..., min_length=5, max_length=3000),
    receipt_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.ORGANIZATION)),
):
    campaign = _campaign_or_404(db, campaign_id)
    _ensure_active(campaign)
    if user.role == Role.ORGANIZATION and campaign.organization_id != user.organization_id:
        raise HTTPException(status_code=403, detail="La campaña pertenece a otra organización")
    exact_amount = parse_money(amount)
    stored = await store_receipt(receipt_file)
    receipt = _create_receipt_model(db, receipt_file, stored, user)
    expense = Expense(
        campaign_id=campaign.id,
        organization_id=campaign.organization_id,
        requested_by_id=user.id,
        concept=concept.strip(),
        description=description.strip(),
        amount=exact_amount,
        receipt_id=receipt.id,
        status=ExpenseStatus.PENDING,
    )
    db.add(expense)
    db.flush()
    record_audit(
        db,
        user,
        "EXPENSE_SUBMITTED",
        "EXPENSE",
        expense.id,
        {
            "campaign_id": campaign.id,
            "amount": exact_amount,
            "concept": expense.concept,
            "receipt_hash": receipt.sha256,
        },
    )
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/expenses/pending", response_model=list[ExpenseOut])
def pending_expenses(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(Role.ADMIN, Role.AUDITOR)),
):
    return list(
        db.scalars(
            select(Expense)
            .where(Expense.status == ExpenseStatus.PENDING)
            .order_by(Expense.created_at)
        )
    )


@router.post("/expenses/{expense_id}/review", response_model=ExpenseOut)
def review_expense(
    expense_id: str,
    payload: ExpenseReview,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.AUDITOR)),
):
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    if expense.status != ExpenseStatus.PENDING:
        raise HTTPException(status_code=409, detail="El gasto ya fue revisado")
    if not payload.approved and not (payload.reason or "").strip():
        raise HTTPException(status_code=422, detail="Debe indicar el motivo del rechazo")
    allocation_ids: list[str] = []
    if payload.approved:
        donated = db.scalar(
            select(func.coalesce(func.sum(Donation.amount), 0)).where(
                Donation.campaign_id == expense.campaign_id
            )
        ) or Decimal("0.00")
        spent = db.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.campaign_id == expense.campaign_id,
                Expense.status == ExpenseStatus.APPROVED,
            )
        ) or Decimal("0.00")
        if Decimal(donated) - Decimal(spent) < expense.amount:
            raise HTTPException(status_code=409, detail="La campaña no tiene saldo suficiente")
        expense.status = ExpenseStatus.APPROVED
        remaining = expense.amount
        donations = db.scalars(
            select(Donation)
            .where(Donation.campaign_id == expense.campaign_id)
            .order_by(Donation.created_at)
        ).all()
        for donation in donations:
            if remaining <= 0:
                break
            used = db.scalar(
                select(func.coalesce(func.sum(Allocation.amount), 0)).where(
                    Allocation.donation_id == donation.id
                )
            ) or Decimal("0.00")
            portion = min(donation.amount - Decimal(used), remaining)
            if portion <= 0:
                continue
            allocation = Allocation(
                donation_id=donation.id,
                expense_id=expense.id,
                amount=portion,
                created_by_id=user.id,
            )
            db.add(allocation)
            db.flush()
            allocation_ids.append(allocation.id)
            remaining -= portion
        if remaining > 0:
            db.rollback()
            raise HTTPException(
                status_code=409, detail="No fue posible asignar el gasto a las donaciones"
            )
        action = "EXPENSE_APPROVED"
    else:
        expense.status = ExpenseStatus.REJECTED
        expense.rejection_reason = payload.reason.strip() if payload.reason else None
        action = "EXPENSE_REJECTED"
    expense.reviewed_by_id = user.id
    expense.reviewed_at = utc_now()
    record_audit(
        db,
        user,
        action,
        "EXPENSE",
        expense.id,
        {
            "status": expense.status.value,
            "reason": expense.rejection_reason,
            "allocation_ids": allocation_ids,
        },
    )
    db.commit()
    db.refresh(expense)
    return expense


@router.post("/allocations", response_model=AllocationOut, status_code=201)
def create_allocation(
    payload: AllocationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.ORGANIZATION)),
):
    donation = db.get(Donation, payload.donation_id)
    expense = db.get(Expense, payload.expense_id)
    if donation is None or expense is None:
        raise HTTPException(status_code=404, detail="Donación o gasto no encontrado")
    if donation.campaign_id != expense.campaign_id:
        raise HTTPException(
            status_code=422, detail="La donación y el gasto deben ser de la misma campaña"
        )
    if expense.status != ExpenseStatus.APPROVED:
        raise HTTPException(status_code=409, detail="Solo se pueden asignar gastos aprobados")
    if user.role == Role.ORGANIZATION and expense.organization_id != user.organization_id:
        raise HTTPException(status_code=403, detail="El gasto pertenece a otra organización")
    amount = parse_money(payload.amount)
    donation_allocated = db.scalar(
        select(func.coalesce(func.sum(Allocation.amount), 0)).where(
            Allocation.donation_id == donation.id
        )
    ) or Decimal("0.00")
    expense_allocated = db.scalar(
        select(func.coalesce(func.sum(Allocation.amount), 0)).where(
            Allocation.expense_id == expense.id
        )
    ) or Decimal("0.00")
    if Decimal(donation_allocated) + amount > donation.amount:
        raise HTTPException(status_code=409, detail="La asignación supera el saldo de la donación")
    if Decimal(expense_allocated) + amount > expense.amount:
        raise HTTPException(status_code=409, detail="La asignación supera el monto del gasto")
    allocation = Allocation(
        donation_id=donation.id,
        expense_id=expense.id,
        amount=amount,
        created_by_id=user.id,
    )
    db.add(allocation)
    db.flush()
    record_audit(
        db,
        user,
        "FUNDS_ALLOCATED",
        "ALLOCATION",
        allocation.id,
        {"donation_id": donation.id, "expense_id": expense.id, "amount": amount},
    )
    db.commit()
    db.refresh(allocation)
    return allocation


@router.post("/expenses/{expense_id}/auto-allocate", response_model=list[AllocationOut])
def auto_allocate(
    expense_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.ORGANIZATION)),
):
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    if expense.status != ExpenseStatus.APPROVED:
        raise HTTPException(status_code=409, detail="El gasto debe estar aprobado")
    if user.role == Role.ORGANIZATION and expense.organization_id != user.organization_id:
        raise HTTPException(status_code=403, detail="El gasto pertenece a otra organización")
    already = db.scalar(
        select(func.coalesce(func.sum(Allocation.amount), 0)).where(
            Allocation.expense_id == expense.id
        )
    ) or Decimal("0.00")
    remaining = expense.amount - Decimal(already)
    created: list[Allocation] = []
    donations = db.scalars(
        select(Donation)
        .where(Donation.campaign_id == expense.campaign_id)
        .order_by(Donation.created_at)
    ).all()
    for donation in donations:
        if remaining <= 0:
            break
        allocated = db.scalar(
            select(func.coalesce(func.sum(Allocation.amount), 0)).where(
                Allocation.donation_id == donation.id
            )
        ) or Decimal("0.00")
        available = donation.amount - Decimal(allocated)
        portion = min(available, remaining)
        if portion <= 0:
            continue
        allocation = Allocation(
            donation_id=donation.id,
            expense_id=expense.id,
            amount=portion,
            created_by_id=user.id,
        )
        db.add(allocation)
        db.flush()
        created.append(allocation)
        remaining -= portion
    if remaining > 0:
        db.rollback()
        raise HTTPException(status_code=409, detail="No existen donaciones sin asignar suficientes")
    record_audit(
        db,
        user,
        "FUNDS_AUTO_ALLOCATED",
        "EXPENSE",
        expense.id,
        {"allocation_ids": [item.id for item in created], "amount": expense.amount},
    )
    db.commit()
    for allocation in created:
        db.refresh(allocation)
    return created
