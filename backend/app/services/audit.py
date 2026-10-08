"""Append-only audit trail writer (section 6.6). Every create/update/delete/
status-change/login/logout goes through this single helper rather than ad hoc
inserts, so the shape is always consistent and nothing is forgotten."""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction


def write_audit_log(
    db: Session,
    *,
    actor_id: uuid.UUID | None,
    action: AuditAction,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip=ip,
        user_agent=user_agent,
    )
    db.add(entry)
    db.flush()
    return entry
