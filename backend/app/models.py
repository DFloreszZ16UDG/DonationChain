"""Persistent entities for the DonationChain domain."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def uuid4_string() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Role(str, Enum):
    ADMIN = "ADMIN"
    ORGANIZATION = "ORGANIZATION"
    DONOR = "DONOR"
    AUDITOR = "AUDITOR"


class CampaignStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class ExpenseStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AnchorStatus(str, Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_string)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(32), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_string)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[Role] = mapped_column(SqlEnum(Role, native_enum=False), nullable=False)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id"))
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Organization | None] = relationship(back_populates="users")


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_string)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    goal_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(
        SqlEnum(CampaignStatus, native_enum=False), default=CampaignStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    organization: Mapped[Organization] = relationship(back_populates="campaigns")
    donations: Mapped[list["Donation"]] = relationship(back_populates="campaign")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="campaign")


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_string)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    uploaded_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Donation(Base):
    __tablename__ = "donations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_string)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    donor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    donor_name: Mapped[str] = mapped_column(String(160), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    receipt_id: Mapped[str | None] = mapped_column(ForeignKey("receipts.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    campaign: Mapped[Campaign] = relationship(back_populates="donations")
    receipt: Mapped[Receipt | None] = relationship()
    allocations: Mapped[list["Allocation"]] = relationship(back_populates="donation")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_string)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id"), index=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    requested_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    concept: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    receipt_id: Mapped[str] = mapped_column(ForeignKey("receipts.id"), unique=True)
    status: Mapped[ExpenseStatus] = mapped_column(
        SqlEnum(ExpenseStatus, native_enum=False), default=ExpenseStatus.PENDING
    )
    reviewed_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    campaign: Mapped[Campaign] = relationship(back_populates="expenses")
    receipt: Mapped[Receipt] = relationship()
    allocations: Mapped[list["Allocation"]] = relationship(back_populates="expense")


class Allocation(Base):
    __tablename__ = "allocations"
    __table_args__ = (UniqueConstraint("donation_id", "expense_id", name="uq_allocation_pair"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_string)
    donation_id: Mapped[str] = mapped_column(ForeignKey("donations.id"), index=True)
    expense_id: Mapped[str] = mapped_column(ForeignKey("expenses.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    donation: Mapped[Donation] = relationship(back_populates="allocations")
    expense: Mapped[Expense] = relationship(back_populates="allocations")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_string)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    details_json: Mapped[str] = mapped_column(Text, nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    entry_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    anchor_status: Mapped[AnchorStatus] = mapped_column(
        SqlEnum(AnchorStatus, native_enum=False), default=AnchorStatus.NOT_CONFIGURED
    )
    blockchain_tx_hash: Mapped[str | None] = mapped_column(String(80))
    blockchain_block_number: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
