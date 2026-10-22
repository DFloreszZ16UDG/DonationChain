"""Tamper-evident audit chain stored in the database."""

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import AnchorStatus, AuditLog, User


def _json_default(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"No se puede serializar {type(value).__name__}")


def canonical_json(value: dict) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=_json_default
    )


def record_audit(
    db: Session,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict,
) -> AuditLog:
    previous = db.scalar(
        select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(1)
    )
    previous_hash = previous.entry_hash if previous else "0" * 64
    created_at = datetime.now(UTC)
    details_json = canonical_json(details)
    payload = canonical_json(
        {
            "actor_id": actor.id if actor else None,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": json.loads(details_json),
            "previous_hash": previous_hash,
            "created_at": created_at,
        }
    )
    entry_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    audit = AuditLog(
        actor_id=actor.id if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details_json=details_json,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
        anchor_status=(
            AnchorStatus.PENDING
            if get_settings().blockchain_writes_enabled
            else AnchorStatus.NOT_CONFIGURED
        ),
        created_at=created_at,
    )
    db.add(audit)
    db.flush()
    return audit


def verify_audit_chain(db: Session) -> tuple[bool, str]:
    entries = list(db.scalars(select(AuditLog).order_by(AuditLog.created_at, AuditLog.id)))
    previous_hash = "0" * 64
    for entry in entries:
        if entry.previous_hash != previous_hash:
            return False, f"Enlace inválido en la entrada {entry.id}"
        payload = canonical_json(
            {
                "actor_id": entry.actor_id,
                "action": entry.action,
                "entity_type": entry.entity_type,
                "entity_id": entry.entity_id,
                "details": json.loads(entry.details_json),
                "previous_hash": entry.previous_hash,
                "created_at": entry.created_at.replace(tzinfo=UTC)
                if entry.created_at.tzinfo is None
                else entry.created_at,
            }
        )
        calculated = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if calculated != entry.entry_hash:
            return False, f"Contenido alterado en la entrada {entry.id}"
        previous_hash = entry.entry_hash
    return True, f"Cadena de auditoría válida ({len(entries)} entradas)"
