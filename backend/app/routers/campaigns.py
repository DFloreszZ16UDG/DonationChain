from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Campaign, CampaignStatus, Donation, Expense, ExpenseStatus, Role, User
from ..schemas import CampaignCreate, CampaignOut, CampaignStatusUpdate
from ..security import require_roles
from ..services.audit import record_audit

router = APIRouter(prefix="/campaigns", tags=["Campañas"])


def campaign_output(db: Session, campaign: Campaign) -> CampaignOut:
    donated = db.scalar(
        select(func.coalesce(func.sum(Donation.amount), 0)).where(
            Donation.campaign_id == campaign.id
        )
    ) or Decimal("0.00")
    spent = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.campaign_id == campaign.id, Expense.status == ExpenseStatus.APPROVED
        )
    ) or Decimal("0.00")
    output = CampaignOut.model_validate(campaign)
    output.donated = Decimal(donated).quantize(Decimal("0.01"))
    output.spent = Decimal(spent).quantize(Decimal("0.01"))
    output.available = (output.donated - output.spent).quantize(Decimal("0.01"))
    return output


@router.get("", response_model=list[CampaignOut])
def list_campaigns(db: Session = Depends(get_db)):
    campaigns = db.scalars(select(Campaign).order_by(Campaign.created_at.desc())).all()
    return [campaign_output(db, campaign) for campaign in campaigns]


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    return campaign_output(db, campaign)


@router.post("", response_model=CampaignOut, status_code=201)
def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.ORGANIZATION)),
):
    organization_id = payload.organization_id if user.role == Role.ADMIN else user.organization_id
    if not organization_id:
        raise HTTPException(status_code=422, detail="Debe indicar una organización")
    campaign = Campaign(
        organization_id=organization_id,
        name=payload.name,
        description=payload.description,
        goal_amount=payload.goal_amount,
        status=CampaignStatus.DRAFT,
    )
    db.add(campaign)
    db.flush()
    record_audit(
        db,
        user,
        "CAMPAIGN_CREATED",
        "CAMPAIGN",
        campaign.id,
        {"name": campaign.name, "goal_amount": campaign.goal_amount},
    )
    db.commit()
    db.refresh(campaign)
    return campaign_output(db, campaign)


@router.patch("/{campaign_id}/status", response_model=CampaignOut)
def update_status(
    campaign_id: str,
    payload: CampaignStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.ORGANIZATION)),
):
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    if user.role == Role.ORGANIZATION and campaign.organization_id != user.organization_id:
        raise HTTPException(status_code=403, detail="La campaña pertenece a otra organización")
    old_status = campaign.status
    campaign.status = payload.status
    record_audit(
        db,
        user,
        "CAMPAIGN_STATUS_CHANGED",
        "CAMPAIGN",
        campaign.id,
        {"from": old_status.value, "to": campaign.status.value},
    )
    db.commit()
    db.refresh(campaign)
    return campaign_output(db, campaign)
