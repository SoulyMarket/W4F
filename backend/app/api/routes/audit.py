import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, UserRole
from app.models.user import User
from app.schemas.audit import AuditLogListOut, AuditLogOut

router = APIRouter(prefix="/audit", tags=["audit"])

_require_admin = require_roles(UserRole.ADMIN)


@router.get("", response_model=AuditLogListOut)
def list_audit_log(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    actor_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    action: AuditAction | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AuditLogListOut:
    query = db.query(AuditLog)
    if actor_id is not None:
        query = query.filter(AuditLog.actor_id == actor_id)
    if entity_type is not None:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action is not None:
        query = query.filter(AuditLog.action == action)
    if date_from is not None:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to is not None:
        query = query.filter(AuditLog.created_at <= date_to)

    total = query.with_entities(func.count(AuditLog.id)).scalar()
    items = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return AuditLogListOut(
        items=[AuditLogOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
