from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User

PASSWORD = "correct horse battery staple"


def make_user(db_session, role=UserRole.ADMIN, email="admin@example.com"):
    user = User(
        full_name="Admin", email=email, password_hash=hash_password(PASSWORD), role=role
    )
    db_session.add(user)
    db_session.flush()
    return user


def auth_headers(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_admin_can_read_audit_log(client, db_session):
    make_user(db_session)
    headers = auth_headers(client, "admin@example.com")  # the login itself writes an audit row

    resp = client.get("/api/v1/audit", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert any(item["action"] == "login" for item in body["items"])


def test_audit_log_filters_by_action(client, db_session):
    make_user(db_session)
    headers = auth_headers(client, "admin@example.com")
    client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": "wrong"}
    )

    resp = client.get("/api/v1/audit?action=login_failed", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert all(item["action"] == "login_failed" for item in body["items"])
    assert body["total"] >= 1


def test_non_admin_cannot_read_audit_log(client, db_session):
    make_user(db_session, role=UserRole.MANAGER, email="manager@example.com")
    headers = auth_headers(client, "manager@example.com")

    resp = client.get("/api/v1/audit", headers=headers)
    assert resp.status_code == 403


def test_audit_log_is_paginated(client, db_session):
    make_user(db_session)
    headers = auth_headers(client, "admin@example.com")

    resp = client.get("/api/v1/audit?page=1&page_size=1", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) <= 1
    assert body["page"] == 1
    assert body["page_size"] == 1
