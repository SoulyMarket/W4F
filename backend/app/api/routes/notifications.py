import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_request_language, require_roles
from app.core.errors import ApiError
from app.db.session import get_db
from app.models.device_token import DeviceToken
from app.models.enums import UserRole
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notifications import DeviceTokenCreate, NotificationListOut, NotificationOut
from app.services.notifications import render_notification_message

router = APIRouter(tags=["notifications"])

_require_any = require_roles(*list(UserRole))


def _to_out(notification: Notification, lang: str) -> NotificationOut:
    return NotificationOut(
        id=notification.id,
        type=notification.type,
        params=notification.params,
        entity_type=notification.entity_type,
        entity_id=notification.entity_id,
        is_read=notification.is_read,
        created_at=notification.created_at,
        message=render_notification_message(notification, lang),
    )


@router.get("/notifications", response_model=NotificationListOut)
def list_notifications(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_any),
    unread_only: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> NotificationListOut:
    lang = get_request_language(request)
    query = db.query(Notification).filter_by(user_id=current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    total = query.with_entities(func.count(Notification.id)).scalar()
    unread_count = (
        db.query(func.count(Notification.id))
        .filter_by(user_id=current_user.id, is_read=False)
        .scalar()
    )
    items = (
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return NotificationListOut(
        items=[_to_out(n, lang) for n in items],
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
    )


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_any),
) -> NotificationOut:
    lang = get_request_language(request)
    notification = (
        db.query(Notification).filter_by(id=notification_id, user_id=current_user.id).first()
    )
    if notification is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            key="errors.not_found",
            lang=lang,
        )
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return _to_out(notification, lang)


@router.post("/devices", status_code=status.HTTP_201_CREATED)
def register_device(
    body: DeviceTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_any),
) -> dict[str, bool]:
    existing = db.query(DeviceToken).filter_by(fcm_token=body.fcm_token).one_or_none()
    if existing:
        existing.user_id = current_user.id
        existing.platform = body.platform
    else:
        db.add(
            DeviceToken(user_id=current_user.id, fcm_token=body.fcm_token, platform=body.platform)
        )
    db.commit()
    return {"ok": True}
