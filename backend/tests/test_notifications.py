from app.core.security import hash_password
from app.models.device_token import DeviceToken
from app.models.enums import NotificationType, UserRole
from app.models.notification import Notification
from app.models.user import User

PASSWORD = "correct horse battery staple"


def make_user(db_session, role, email):
    user = User(full_name="U", email=email, password_hash=hash_password(PASSWORD), role=role)
    db_session.add(user)
    db_session.flush()
    return user


def auth_headers(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_user_sees_only_their_own_notifications(client, db_session):
    user_a = make_user(db_session, UserRole.MOQADDEM, "a@example.com")
    user_b = make_user(db_session, UserRole.MOQADDEM, "b@example.com")
    db_session.add(
        Notification(
            user_id=user_a.id,
            type=NotificationType.VALIDATED,
            params={"douar": "Test"},
            entity_type="report",
            entity_id=user_a.id,
        )
    )
    db_session.add(
        Notification(
            user_id=user_b.id,
            type=NotificationType.VALIDATED,
            params={"douar": "Other"},
            entity_type="report",
            entity_id=user_b.id,
        )
    )
    db_session.flush()
    headers = auth_headers(client, "a@example.com")

    resp = client.get("/api/v1/notifications", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["params"]["douar"] == "Test"


def test_notification_message_is_localized(client, db_session):
    user = make_user(db_session, UserRole.MOQADDEM, "c@example.com")
    db_session.add(
        Notification(
            user_id=user.id,
            type=NotificationType.VALIDATED,
            params={"douar": "Douar X"},
            entity_type="report",
            entity_id=user.id,
        )
    )
    db_session.flush()
    headers = auth_headers(client, "c@example.com")

    resp = client.get("/api/v1/notifications", headers=headers)
    assert resp.status_code == 200
    message = resp.json()["items"][0]["message"]
    assert "Douar X" in message


def test_unread_count_and_mark_read(client, db_session):
    user = make_user(db_session, UserRole.MOQADDEM, "d@example.com")
    n1 = Notification(
        user_id=user.id,
        type=NotificationType.VALIDATED,
        params={"douar": "D1"},
        entity_type="report",
        entity_id=user.id,
    )
    n2 = Notification(
        user_id=user.id,
        type=NotificationType.RECHECK_REQUESTED,
        params={"douar": "D2"},
        entity_type="report",
        entity_id=user.id,
    )
    db_session.add_all([n1, n2])
    db_session.flush()
    headers = auth_headers(client, "d@example.com")

    resp = client.get("/api/v1/notifications", headers=headers)
    assert resp.json()["unread_count"] == 2

    mark_resp = client.post(f"/api/v1/notifications/{n1.id}/read", headers=headers)
    assert mark_resp.status_code == 200
    assert mark_resp.json()["is_read"] is True

    resp2 = client.get("/api/v1/notifications", headers=headers)
    assert resp2.json()["unread_count"] == 1


def test_cannot_mark_other_users_notification_as_read(client, db_session):
    make_user(db_session, UserRole.MOQADDEM, "e@example.com")
    user_b = make_user(db_session, UserRole.MOQADDEM, "f@example.com")
    n = Notification(
        user_id=user_b.id,
        type=NotificationType.VALIDATED,
        params={"douar": "X"},
        entity_type="report",
        entity_id=user_b.id,
    )
    db_session.add(n)
    db_session.flush()
    headers = auth_headers(client, "e@example.com")

    resp = client.post(f"/api/v1/notifications/{n.id}/read", headers=headers)
    assert resp.status_code == 404


def test_register_device_token(client, db_session):
    user = make_user(db_session, UserRole.MOQADDEM, "g@example.com")
    headers = auth_headers(client, "g@example.com")

    resp = client.post(
        "/api/v1/devices",
        json={"fcm_token": "abc123token", "platform": "android"},
        headers=headers,
    )
    assert resp.status_code == 201

    row = db_session.query(DeviceToken).filter_by(fcm_token="abc123token").one()
    assert row.user_id == user.id
    assert row.platform == "android"


def test_register_device_token_upserts_on_duplicate_token(client, db_session):
    make_user(db_session, UserRole.MOQADDEM, "h@example.com")
    user_b = make_user(db_session, UserRole.MOQADDEM, "i@example.com")

    headers_a = auth_headers(client, "h@example.com")
    client.post(
        "/api/v1/devices",
        json={"fcm_token": "shared-token", "platform": "android"},
        headers=headers_a,
    )

    headers_b = auth_headers(client, "i@example.com")
    resp = client.post(
        "/api/v1/devices", json={"fcm_token": "shared-token", "platform": "ios"}, headers=headers_b
    )
    assert resp.status_code == 201

    rows = db_session.query(DeviceToken).filter_by(fcm_token="shared-token").all()
    assert len(rows) == 1
    assert rows[0].user_id == user_b.id
    assert rows[0].platform == "ios"
