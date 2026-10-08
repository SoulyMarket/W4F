from app.core.security import hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User

PASSWORD = "correct horse battery staple"


def make_user(db_session, role=UserRole.ADMIN, email="admin@example.com", **overrides):
    defaults = dict(
        full_name="Admin",
        email=email,
        password_hash=hash_password(PASSWORD),
        role=role,
        is_active=True,
    )
    defaults.update(overrides)
    user = User(**defaults)
    db_session.add(user)
    db_session.flush()
    return user


def auth_headers(client, email):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_admin_can_create_user(client, db_session):
    make_user(db_session)
    headers = auth_headers(client, "admin@example.com")

    resp = client.post(
        "/api/v1/users",
        json={
            "full_name": "New Expert",
            "email": "newexpert@example.com",
            "password": "a strong password",
            "role": "expert",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "newexpert@example.com"
    assert body["role"] == "expert"
    assert "password" not in body
    assert "password_hash" not in body

    created = db_session.query(User).filter_by(email="newexpert@example.com").one()
    assert verify_password("a strong password", created.password_hash)


def test_create_user_lowercases_email(client, db_session):
    make_user(db_session)
    headers = auth_headers(client, "admin@example.com")

    resp = client.post(
        "/api/v1/users",
        json={
            "full_name": "Mixed Case",
            "email": "MixedCase@Example.com",
            "password": "a strong password",
            "role": "manager",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "mixedcase@example.com"


def test_create_user_with_duplicate_email_returns_409(client, db_session):
    make_user(db_session)
    make_user(db_session, role=UserRole.MANAGER, email="dup@example.com")
    headers = auth_headers(client, "admin@example.com")

    resp = client.post(
        "/api/v1/users",
        json={
            "full_name": "Dup",
            "email": "dup@example.com",
            "password": "a strong password",
            "role": "expert",
        },
        headers=headers,
    )
    assert resp.status_code == 409


def test_non_admin_cannot_create_user(client, db_session):
    make_user(db_session, role=UserRole.MANAGER, email="manager@example.com")
    headers = auth_headers(client, "manager@example.com")

    resp = client.post(
        "/api/v1/users",
        json={
            "full_name": "Nope",
            "email": "nope@example.com",
            "password": "a strong password",
            "role": "expert",
        },
        headers=headers,
    )
    assert resp.status_code == 403


def test_admin_can_list_users(client, db_session):
    make_user(db_session)
    make_user(db_session, role=UserRole.MANAGER, email="m1@example.com")
    make_user(db_session, role=UserRole.EXPERT, email="e1@example.com")
    headers = auth_headers(client, "admin@example.com")

    resp = client.get("/api/v1/users", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3


def test_admin_can_get_user_by_id(client, db_session):
    make_user(db_session)
    target = make_user(db_session, role=UserRole.EXPERT, email="target@example.com")
    headers = auth_headers(client, "admin@example.com")

    resp = client.get(f"/api/v1/users/{target.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "target@example.com"


def test_admin_can_update_user(client, db_session):
    make_user(db_session)
    target = make_user(db_session, role=UserRole.EXPERT, email="update-me@example.com")
    headers = auth_headers(client, "admin@example.com")

    resp = client.patch(
        f"/api/v1/users/{target.id}",
        json={"full_name": "Updated Name", "role": "manager"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "Updated Name"
    assert body["role"] == "manager"


def test_admin_can_deactivate_user(client, db_session):
    make_user(db_session)
    target = make_user(db_session, role=UserRole.EXPERT, email="deactivate-me@example.com")
    db_session.flush()
    headers = auth_headers(client, "admin@example.com")

    resp = client.post(f"/api/v1/users/{target.id}/deactivate", headers=headers)
    assert resp.status_code == 200

    db_session.refresh(target)
    assert target.is_active is False

    login_attempt = client.post(
        "/api/v1/auth/login",
        json={"email": "deactivate-me@example.com", "password": PASSWORD},
    )
    assert login_attempt.status_code == 403


def test_admin_can_reset_user_password(client, db_session):
    make_user(db_session)
    target = make_user(db_session, role=UserRole.EXPERT, email="resetme@example.com")
    db_session.flush()
    headers = auth_headers(client, "admin@example.com")

    resp = client.post(f"/api/v1/users/{target.id}/reset-password", headers=headers)
    assert resp.status_code == 200
    new_password = resp.json()["temporary_password"]
    assert len(new_password) >= 12

    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "resetme@example.com", "password": new_password}
    )
    assert login_resp.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login", json={"email": "resetme@example.com", "password": PASSWORD}
    )
    assert old_login.status_code == 401


def test_write_endpoints_produce_audit_rows_with_old_and_new_values(client, db_session):
    from app.models.audit_log import AuditLog
    from app.models.enums import AuditAction

    make_user(db_session)
    target = make_user(db_session, role=UserRole.EXPERT, email="audited@example.com")
    db_session.flush()
    headers = auth_headers(client, "admin@example.com")

    client.patch(
        f"/api/v1/users/{target.id}", json={"full_name": "Audited New Name"}, headers=headers
    )

    entry = (
        db_session.query(AuditLog)
        .filter_by(entity_type="user", entity_id=target.id, action=AuditAction.UPDATE)
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert entry is not None
    # make_user()'s full_name default is "Admin" unless overridden — it wasn't here.
    assert entry.old_value["full_name"] == "Admin"
    assert entry.new_value["full_name"] == "Audited New Name"
