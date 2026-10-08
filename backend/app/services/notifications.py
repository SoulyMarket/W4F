"""Creates Notification rows (section 5's "Notifications" trigger list).
Title/body text is never stored — only `type` + `params`, rendered in the
recipient's language at read time (section 2.1)."""

import uuid

from sqlalchemy.orm import Session

from app.models.enums import NotificationType, UserRole
from app.models.notification import Notification
from app.models.user import User


def notify_user(
    db: Session,
    *,
    user_id: uuid.UUID,
    type: NotificationType,
    params: dict,
    entity_type: str,
    entity_id: uuid.UUID,
) -> Notification:
    notification = Notification(
        user_id=user_id, type=type, params=params, entity_type=entity_type, entity_id=entity_id
    )
    db.add(notification)
    return notification


def notify_all_managers(
    db: Session,
    *,
    type: NotificationType,
    params: dict,
    entity_type: str,
    entity_id: uuid.UUID,
) -> list[Notification]:
    """Section 5 doesn't scope the "validated"/project notifications to
    managers of the report's own territory — simplification ruling: every
    manager gets notified (see PROGRESS.md). Fine for the prototype's
    scale; a territory-filtered fan-out is one query away if this needs
    tightening later."""
    manager_ids = [u.id for u in db.query(User.id).filter_by(role=UserRole.MANAGER).all()]
    return [
        notify_user(
            db, user_id=mid, type=type, params=params, entity_type=entity_type, entity_id=entity_id
        )
        for mid in manager_ids
    ]
