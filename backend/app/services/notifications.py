"""Creates Notification rows (section 5's "Notifications" trigger list).
Title/body text is never stored — only `type` + `params`, rendered in the
recipient's language at read time (section 2.1)."""

import uuid

from sqlalchemy.orm import Session

from app.i18n import t
from app.models.enums import NotificationType, UserRole
from app.models.notification import Notification
from app.models.user import User
from app.services.territory_scope import get_accessible_territory_ids


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


def notify_territory_experts(
    db: Session,
    *,
    territory_id: uuid.UUID,
    type: NotificationType,
    params: dict,
    entity_type: str,
    entity_id: uuid.UUID,
) -> list[Notification]:
    """Section 5's "new report" trigger: experts of the report's territory,
    not every expert globally (unlike the manager fan-out above) — an
    expert is "of" `territory_id` if it's in their accessible set (their own
    assignment, or one of its ancestors following the same rule
    `territory_scope_filter` uses everywhere else)."""
    experts = db.query(User).filter_by(role=UserRole.EXPERT).all()
    recipients = [e for e in experts if territory_id in get_accessible_territory_ids(db, e)]
    return [
        notify_user(
            db,
            user_id=e.id,
            type=type,
            params=params,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        for e in recipients
    ]


def render_notification_message(notification: Notification, lang: str) -> str:
    """Single shared renderer for `GET /notifications` and `GET /sync/pull`
    (previously duplicated in both routes, see PROGRESS.md) — one place to
    fix when a param needs a second i18n lookup before substitution, like
    `project_status_changed`'s `status`, a raw section-4 enum value that
    would otherwise sit untranslated inside an Arabic/French sentence
    (e.g. "...إلى in_progress")."""
    params = dict(notification.params)
    if notification.type == NotificationType.PROJECT_STATUS_CHANGED and "status" in params:
        params["status"] = t(f"enum.project_status.{params['status']}", lang)
    return t(f"notifications.{notification.type.value}", lang, **params)
