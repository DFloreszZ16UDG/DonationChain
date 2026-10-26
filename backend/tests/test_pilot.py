from decimal import Decimal

from app.database import SessionLocal
from app.models import Allocation, Expense, ExpenseStatus, Receipt
from app.services.receipts import receipt_path


def test_complete_donation_expense_and_audit_flow(client, headers, active_campaign, png_file):
    donation_response = client.post(
        f"/api/campaigns/{active_campaign}/donations",
        headers=headers["donor"],
        data={"amount": "1000.10", "donor_name": "Donante verificable"},
        files={"receipt_file": ("transferencia.png", png_file, "image/png")},
    )
    assert donation_response.status_code == 201, donation_response.text
    donation = donation_response.json()
    assert Decimal(donation["amount"]) == Decimal("1000.10")

    expense_response = client.post(
        f"/api/campaigns/{active_campaign}/expenses",
        headers=headers["org"],
        data={
            "amount": "200.05",
            "concept": "Compra de alimentos",
            "description": "Despensas para veinte familias",
        },
        files={"receipt_file": ("factura.png", png_file, "image/png")},
    )
    assert expense_response.status_code == 201, expense_response.text
    expense = expense_response.json()
    assert expense["status"] == "PENDING"

    review = client.post(
        f"/api/expenses/{expense['id']}/review",
        headers=headers["auditor"],
        json={"approved": True},
    )
    assert review.status_code == 200, review.text
    assert review.json()["status"] == "APPROVED"

    campaign = client.get(f"/api/campaigns/{active_campaign}").json()
    assert Decimal(campaign["donated"]) == Decimal("1000.10")
    assert Decimal(campaign["spent"]) == Decimal("200.05")
    assert Decimal(campaign["available"]) == Decimal("800.05")

    with SessionLocal() as db:
        stored_expense = db.get(Expense, expense["id"])
        assert stored_expense.status == ExpenseStatus.APPROVED
        allocation = db.query(Allocation).filter_by(expense_id=expense["id"]).one()
        assert allocation.donation_id == donation["id"]
        assert allocation.amount == Decimal("200.05")

    trace = client.get(
        f"/api/donations/{donation['id']}/trace",
        headers=headers["donor"],
    )
    assert trace.status_code == 200
    assert Decimal(trace.json()["allocated"]) == Decimal("200.05")
    assert Decimal(trace.json()["unallocated"]) == Decimal("800.05")
    assert trace.json()["allocations"][0]["concept"] == "Compra de alimentos"
    assert trace.json()["audit_id"]
    assert len(trace.json()["audit_hash"]) == 64

    acknowledgement = client.get(
        f"/api/donations/{donation['id']}/acknowledgement.pdf",
        headers=headers["donor"],
    )
    assert acknowledgement.status_code == 200
    assert acknowledgement.headers["content-type"] == "application/pdf"
    assert "attachment" in acknowledgement.headers["content-disposition"]
    assert acknowledgement.content.startswith(b"%PDF")

    blockchain_check = client.get(
        f"/api/blockchain/verify/{trace.json()['audit_id']}"
    )
    assert blockchain_check.status_code == 503
    assert "Smart Contract" in blockchain_check.json()["detail"]

    audit = client.get("/api/audit/verify", headers=headers["auditor"])
    assert audit.status_code == 200
    assert audit.json()["valid"] is True

    verify = client.post(
        f"/api/receipts/{expense['receipt_id']}/verify",
        files={"receipt_file": ("factura.png", png_file, "image/png")},
    )
    assert verify.status_code == 200
    assert verify.json()["matches"] is True


def test_decimal_validation_rejects_rounding(client, headers, active_campaign):
    response = client.post(
        f"/api/campaigns/{active_campaign}/donations",
        headers=headers["donor"],
        data={"amount": "10.999", "donor_name": "Prueba"},
    )
    assert response.status_code == 422
    assert "dos decimales" in response.json()["detail"]


def test_role_protection_and_authentication(client, headers, active_campaign, png_file):
    anonymous = client.get("/api/audit")
    assert anonymous.status_code == 401

    donor_expense = client.post(
        f"/api/campaigns/{active_campaign}/expenses",
        headers=headers["donor"],
        data={
            "amount": "50.00",
            "concept": "No autorizado",
            "description": "Este intento debe ser bloqueado",
        },
        files={"receipt_file": ("proof.png", png_file, "image/png")},
    )
    assert donor_expense.status_code == 403


def test_receipt_rejects_fake_content_and_sanitizes_filename(
    client, headers, active_campaign, png_file
):
    fake = client.post(
        f"/api/campaigns/{active_campaign}/donations",
        headers=headers["donor"],
        data={"amount": "20.00", "donor_name": "Prueba"},
        files={"receipt_file": ("fake.pdf", b"not a pdf", "application/pdf")},
    )
    assert fake.status_code == 415

    safe = client.post(
        f"/api/campaigns/{active_campaign}/donations",
        headers=headers["donor"],
        data={"amount": "20.00", "donor_name": "Prueba"},
        files={"receipt_file": ("../../danger.png", png_file, "image/png")},
    )
    assert safe.status_code == 201
    with SessionLocal() as db:
        receipt = db.get(Receipt, safe.json()["receipt_id"])
        assert receipt.original_name == "danger.png"
        assert receipt_path(receipt.stored_name).exists()
        assert ".." not in receipt.stored_name


def test_insufficient_balance_prevents_expense_approval(client, headers, active_campaign, png_file):
    client.post(
        f"/api/campaigns/{active_campaign}/donations",
        headers=headers["donor"],
        data={"amount": "100.00", "donor_name": "Donante"},
    )
    expense = client.post(
        f"/api/campaigns/{active_campaign}/expenses",
        headers=headers["org"],
        data={
            "amount": "101.00",
            "concept": "Exceso",
            "description": "Monto superior al saldo disponible",
        },
        files={"receipt_file": ("expense.png", png_file, "image/png")},
    ).json()
    review = client.post(
        f"/api/expenses/{expense['id']}/review",
        headers=headers["auditor"],
        json={"approved": True},
    )
    assert review.status_code == 409
    assert "saldo suficiente" in review.json()["detail"]
