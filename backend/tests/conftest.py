import os
import tempfile
from pathlib import Path

TEST_ROOT = Path(tempfile.mkdtemp(prefix="donationchain-tests-"))
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_ROOT / 'test.db').as_posix()}"
os.environ["RECEIPT_DIRECTORY"] = str(TEST_ROOT / "receipts")
os.environ["JWT_SECRET"] = "test-secret-that-is-never-used-in-production"
os.environ["BLOCKCHAIN_RPC_URL"] = ""

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Organization, Role, User
from app.security import hash_password

PASSWORD = "SecureTest123!"


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        organization = Organization(
            name="Organización de pruebas",
            legal_name="Organización de Pruebas A.C.",
            tax_id="TEST010101AA1",
        )
        db.add(organization)
        db.flush()
        db.add_all(
            [
                User(
                    email="admin@example.com",
                    full_name="Admin",
                    password_hash=hash_password(PASSWORD),
                    role=Role.ADMIN,
                ),
                User(
                    email="auditor@example.com",
                    full_name="Auditor",
                    password_hash=hash_password(PASSWORD),
                    role=Role.AUDITOR,
                ),
                User(
                    email="donor@example.com",
                    full_name="Donor",
                    password_hash=hash_password(PASSWORD),
                    role=Role.DONOR,
                ),
                User(
                    email="org@example.com",
                    full_name="Organization",
                    password_hash=hash_password(PASSWORD),
                    role=Role.ORGANIZATION,
                    organization_id=organization.id,
                ),
            ]
        )
        db.commit()
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def headers(client):
    return {
        "admin": auth_headers(client, "admin@example.com"),
        "auditor": auth_headers(client, "auditor@example.com"),
        "donor": auth_headers(client, "donor@example.com"),
        "org": auth_headers(client, "org@example.com"),
    }


@pytest.fixture
def organization_id():
    with SessionLocal() as db:
        return db.query(Organization).first().id


@pytest.fixture
def active_campaign(client, headers, organization_id):
    response = client.post(
        "/api/campaigns",
        headers=headers["admin"],
        json={
            "organization_id": organization_id,
            "name": "Campaña segura",
            "description": "Campaña utilizada para las pruebas integrales del sistema.",
            "goal_amount": "10000.00",
        },
    )
    assert response.status_code == 201, response.text
    campaign_id = response.json()["id"]
    activated = client.patch(
        f"/api/campaigns/{campaign_id}/status",
        headers=headers["admin"],
        json={"status": "ACTIVE"},
    )
    assert activated.status_code == 200, activated.text
    return campaign_id


@pytest.fixture
def png_file():
    # A valid 1x1 transparent PNG.
    import base64

    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    )
