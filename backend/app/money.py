"""Exact monetary parsing and validation."""

from decimal import Decimal, InvalidOperation

from fastapi import HTTPException

CENT = Decimal("0.01")
MAX_MONEY = Decimal("9999999999999999.99")


def parse_money(value: str | Decimal) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise HTTPException(
            status_code=422, detail="El monto debe ser un número decimal válido"
        ) from exc
    if not amount.is_finite() or amount <= 0:
        raise HTTPException(status_code=422, detail="El monto debe ser mayor que cero")
    if amount > MAX_MONEY:
        raise HTTPException(status_code=422, detail="El monto excede el máximo permitido")
    if amount.as_tuple().exponent < -2:
        raise HTTPException(status_code=422, detail="El monto solo puede tener dos decimales")
    return amount.quantize(CENT)
