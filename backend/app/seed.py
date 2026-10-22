"""Development-only seed data for the local pilot."""

import os
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Campaign, CampaignStatus, Organization, Role, User
from .security import hash_password


def seed_development_data(db: Session) -> None:
    demo_password = os.getenv("DEMO_PASSWORD")
    if not demo_password:
        return
    if db.scalar(select(User).limit(1)) is not None:
        return

    organization = Organization(
        name="Fundación Manos Abiertas",
        legal_name="Fundación Manos Abiertas A.C.",
        tax_id="FMA260101AB1",
    )
    db.add(organization)
    db.flush()

    users = [
        User(
            email="admin@donationchain.example.com",
            full_name="Administración DonationChain",
            password_hash=hash_password(demo_password),
            role=Role.ADMIN,
        ),
        User(
            email="organizacion@donationchain.example.com",
            full_name="Responsable de organización",
            password_hash=hash_password(demo_password),
            role=Role.ORGANIZATION,
            organization_id=organization.id,
        ),
        User(
            email="auditor@donationchain.example.com",
            full_name="Auditor independiente",
            password_hash=hash_password(demo_password),
            role=Role.AUDITOR,
        ),
        User(
            email="donante@donationchain.example.com",
            full_name="Donante de demostración",
            password_hash=hash_password(demo_password),
            role=Role.DONOR,
        ),
    ]
    db.add_all(users)
    db.add(
        Campaign(
            organization_id=organization.id,
            name="Apoyo para familias afectadas",
            description=(
                "Campaña piloto para comprar alimentos, medicamentos y artículos esenciales "
                "con trazabilidad pública de cada gasto."
            ),
            goal_amount=Decimal("50000.00"),
            status=CampaignStatus.ACTIVE,
        )
    )
    db.commit()
