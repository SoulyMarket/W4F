"""Firebase Cloud Messaging sender (section 9 step 2.1). No-op whenever
Firebase isn't configured (`FCM_CREDENTIALS_JSON` empty) — the normal state
in every environment this has actually run in so far, since no real
Firebase project exists here; wiring this into the notification triggers
and verifying real delivery is step 2.5's job, once the Android app has its
own Firebase project to receive against.

Never raises: a push is best-effort delivery on top of the DB notification
row (already written by the caller), not the thing the API request's
success depends on.
"""

import json
import logging
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import Settings

logger = logging.getLogger(__name__)


@lru_cache
def _firebase_app(credentials_json: str) -> firebase_admin.App | None:
    if not credentials_json:
        return None
    cert = credentials.Certificate(json.loads(credentials_json))
    return firebase_admin.initialize_app(cert, name=f"w4f-fcm-{hash(credentials_json)}")


def send_push(
    settings: Settings,
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> None:
    """Sends one push notification to every token in `tokens`. `title`/`body`
    must already be localized for the recipient (there's no later render
    step for an OS tray notification, unlike the DB-stored Notification rows
    elsewhere in this codebase)."""
    if not tokens:
        return
    app = _firebase_app(settings.fcm_credentials_json)
    if app is None:
        logger.info("FCM not configured — skipping push to %d device(s)", len(tokens))
        return
    notification = messaging.Notification(title=title, body=body)
    messages = [
        messaging.Message(notification=notification, data=data or {}, token=token)
        for token in tokens
    ]
    try:
        messaging.send_each(messages, app=app)
    except Exception:
        logger.exception("FCM push failed")
