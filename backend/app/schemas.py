"""Validated API input and output models."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from .models import AnchorStatus, CampaignStatus, ExpenseStatus, Role

Money = Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=2)]
NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=240)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OrganizationCreate(BaseModel):
    name: NonEmpty
    legal_name: NonEmpty
    tax_id: str | None = Field(default=None, max_length=32)


class OrganizationOut(ORMModel):
    id: str
    name: str
    legal_name: str
    tax_id: str | None
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    full_name: NonEmpty
    password: str = Field(min_length=10, max_length=128)


class UserAdminCreate(UserCreate):
    role: Role
    organization_id: str | None = None


class UserOut(ORMModel):
    id: str
    email: EmailStr
    full_name: str
    role: Role
    organization_id: str | None
    active: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CampaignCreate(BaseModel):
    organization_id: str | None = None
    name: NonEmpty
    description: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=10, max_length=3000)
    ]
    goal_amount: Money


class CampaignStatusUpdate(BaseModel):
    status: CampaignStatus


class CampaignOut(ORMModel):
    id: str
    organization_id: str
    name: str
    description: str
    goal_amount: Decimal
    status: CampaignStatus
    created_at: datetime
    donated: Decimal = Decimal("0.00")
    spent: Decimal = Decimal("0.00")
    available: Decimal = Decimal("0.00")


class ReceiptOut(ORMModel):
    id: str
    original_name: str
    mime_type: str
    size_bytes: int
    sha256: str
    created_at: datetime


class DonationOut(ORMModel):
    id: str
    campaign_id: str
    donor_id: str | None
    donor_name: str
    amount: Decimal
    receipt_id: str | None
    created_at: datetime


class DonationAllocationTrace(BaseModel):
    allocation_id: str
    expense_id: str
    concept: str
    description: str
    amount: Decimal
    status: ExpenseStatus
    created_at: datetime


class DonationTrace(BaseModel):
    donation: DonationOut
    campaign_name: str
    allocated: Decimal
    unallocated: Decimal
    audit_id: str | None
    audit_hash: str | None
    anchor_status: AnchorStatus | None
    blockchain_tx_hash: str | None
    blockchain_block_number: int | None
    allocations: list[DonationAllocationTrace]


class ExpenseOut(ORMModel):
    id: str
    campaign_id: str
    organization_id: str
    requested_by_id: str
    concept: str
    description: str
    amount: Decimal
    receipt_id: str
    status: ExpenseStatus
    reviewed_by_id: str | None
    reviewed_at: datetime | None
    rejection_reason: str | None
    created_at: datetime


class ExpenseReview(BaseModel):
    approved: bool
    reason: str | None = Field(default=None, max_length=1000)


class AllocationCreate(BaseModel):
    donation_id: str
    expense_id: str
    amount: Money


class AllocationOut(ORMModel):
    id: str
    donation_id: str
    expense_id: str
    amount: Decimal
    created_by_id: str
    created_at: datetime


class ReceiptVerification(BaseModel):
    receipt_id: str
    expected_sha256: str
    uploaded_sha256: str
    matches: bool


class AuditOut(ORMModel):
    id: str
    actor_id: str | None
    action: str
    entity_type: str
    entity_id: str
    details_json: str
    previous_hash: str
    entry_hash: str
    anchor_status: AnchorStatus
    blockchain_tx_hash: str | None
    blockchain_block_number: int | None
    created_at: datetime


class BlockchainStatus(BaseModel):
    network: str
    chain_id: int
    rpc_connected: bool
    latest_block: int | None
    contract_configured: bool
    writes_enabled: bool
    explorer_url: str
    message: str


class BlockchainVerification(BaseModel):
    audit_id: str
    record_id: str
    expected_hash: str
    on_chain_hash: str | None
    anchored: bool
    matches: bool
    writer: str | None
    timestamp: int | None
    metadata_uri: str | None
    blockchain_tx_hash: str | None
    blockchain_block_number: int | None
    explorer_url: str


class TimelineEvent(BaseModel):
    id: str
    event_type: str
    title: str
    description: str
    amount: Decimal | None
    status: str
    receipt_id: str | None
    receipt_hash: str | None
    created_at: datetime


class AuditVerification(BaseModel):
    valid: bool
    message: str
