from datetime import UTC, datetime, timedelta

from app.core.security import hash_password, hash_refresh_token
from app.models.enums import UserRole
from app.models.refresh_token import RefreshToken
from app.models.user import User

PASSWORD = "correct horse battery staple"


def make_user(db_session, role=UserRole.MANAGER, is_active=True, **overrides):
    defaults = dict(
        full_name="Test User",
        email="user@example.com",
        password_hash=hash_password(PASSWORD),
        role=role,
        is_active=is_active,
    )
    defaults.update(overrides)
    user = User(**defaults)
    db_session.add(user)
    db_session.flush()
    return user


def test_login_with_valid_credentials_returns_token_pair(client, db_session):
    make_user(db_session, email="valid@example.com")
    db_session.flush()

    response = client.post(
        "/api/v1/auth/login", json={"email": "valid@example.com", "password": PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_with_wrong_password_returns_401(client, db_session):
    make_user(db_session, email="wrongpw@example.com")
    db_session.flush()

    response = client.post(
        "/api/v1/auth/login", json={"email": "wrongpw@example.com", "password": "nope nope nope"}
    )
    assert response.status_code == 401


def test_login_increments_failed_count_and_locks_after_5_failures(client, db_session):
    user = make_user(db_session, email="lockout@example.com")
    db_session.flush()

    for _ in range(5):
        client.post(
            "/api/v1/auth/login", json={"email": "lockout@example.com", "password": "wrong"}
        )

    db_session.refresh(user)
    assert user.failed_login_count == 5
    assert user.locked_until is not None
    assert user.locked_until > datetime.now(UTC)

    # 6th attempt, even with the CORRECT password, is rejected while locked.
    response = client.post(
        "/api/v1/auth/login", json={"email": "lockout@example.com", "password": PASSWORD}
    )
    assert response.status_code == 401


def test_login_with_nonexistent_email_returns_401(client, db_session):
    response = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever123"}
    )
    assert response.status_code == 401


def test_deactivated_user_cannot_log_in(client, db_session):
    make_user(db_session, email="inactive@example.com", is_active=False)
    db_session.flush()

    response = client.post(
        "/api/v1/auth/login", json={"email": "inactive@example.com", "password": PASSWORD}
    )
    assert response.status_code in (401, 403)


def test_successful_login_resets_failed_count(client, db_session):
    user = make_user(db_session, email="reset@example.com")
    user.failed_login_count = 3
    db_session.flush()

    response = client.post(
        "/api/v1/auth/login", json={"email": "reset@example.com", "password": PASSWORD}
    )
    assert response.status_code == 200
    db_session.refresh(user)
    assert user.failed_login_count == 0
    assert user.last_login_at is not None


def test_refresh_token_days_differ_by_role(client, db_session):
    make_user(db_session, email="moqaddem@example.com", role=UserRole.MOQADDEM)
    db_session.flush()
    resp = client.post(
        "/api/v1/auth/login", json={"email": "moqaddem@example.com", "password": PASSWORD}
    )
    refresh_token = resp.json()["refresh_token"]
    row = (
        db_session.query(RefreshToken)
        .filter_by(token_hash=hash_refresh_token(refresh_token))
        .one()
    )
    days_left = (row.expires_at - datetime.now(UTC)).days
    assert days_left >= 29  # ~30 days for moqaddem


def test_refresh_rotates_token(client, db_session):
    make_user(db_session, email="rotate@example.com")
    db_session.flush()
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "rotate@example.com", "password": PASSWORD}
    )
    old_refresh = login_resp.json()["refresh_token"]

    refresh_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert new_tokens["refresh_token"] != old_refresh

    old_row = (
        db_session.query(RefreshToken).filter_by(token_hash=hash_refresh_token(old_refresh)).one()
    )
    assert old_row.revoked_at is not None


def test_reusing_rotated_refresh_token_revokes_whole_family(client, db_session):
    make_user(db_session, email="reuse@example.com")
    db_session.flush()
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "reuse@example.com", "password": PASSWORD}
    )
    first_refresh = login_resp.json()["refresh_token"]

    first_rotation = client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    second_refresh = first_rotation.json()["refresh_token"]

    # Reuse the already-rotated (now revoked) first token.
    reuse_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert reuse_resp.status_code == 401

    # The entire family — including the token issued by the first rotation — is now dead.
    second_use_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": second_refresh})
    assert second_use_resp.status_code == 401


def test_refresh_with_unknown_token_returns_401(client, db_session):
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 401


def test_refresh_with_expired_token_returns_401(client, db_session):
    user = make_user(db_session, email="expired@example.com")
    db_session.flush()
    token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token("expired-token-value"),
        family_id=user.id,
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    db_session.add(token)
    db_session.flush()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "expired-token-value"})
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, db_session):
    make_user(db_session, email="me@example.com", full_name="Me Person")
    db_session.flush()
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "me@example.com", "password": PASSWORD}
    )
    access_token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "me@example.com"
    assert body["full_name"] == "Me Person"
    assert body["territories"] == []


def test_logout_revokes_refresh_token(client, db_session):
    make_user(db_session, email="logout@example.com")
    db_session.flush()
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "logout@example.com", "password": PASSWORD}
    )
    tokens = login_resp.json()

    logout_resp = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert logout_resp.status_code == 200

    refresh_resp = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_resp.status_code == 401


def test_logout_all_revokes_every_session(client, db_session):
    make_user(db_session, email="logoutall@example.com")
    db_session.flush()
    login1 = client.post(
        "/api/v1/auth/login", json={"email": "logoutall@example.com", "password": PASSWORD}
    ).json()
    login2 = client.post(
        "/api/v1/auth/login", json={"email": "logoutall@example.com", "password": PASSWORD}
    ).json()

    resp = client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {login1['access_token']}"},
    )
    assert resp.status_code == 200

    for tokens in (login1, login2):
        refresh_resp = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_resp.status_code == 401


def test_change_password_with_correct_current_password(client, db_session):
    make_user(db_session, email="changepw@example.com")
    db_session.flush()
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "changepw@example.com", "password": PASSWORD}
    )
    access_token = login_resp.json()["access_token"]

    resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": PASSWORD, "new_password": "a brand new password"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200

    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "changepw@example.com", "password": "a brand new password"},
    )
    assert new_login.status_code == 200


def test_change_password_with_wrong_current_password_fails(client, db_session):
    make_user(db_session, email="changepwfail@example.com")
    db_session.flush()
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "changepwfail@example.com", "password": PASSWORD}
    )
    access_token = login_resp.json()["access_token"]

    resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "totally wrong", "new_password": "a brand new password"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 400


def test_change_password_rejects_short_new_password(client, db_session):
    make_user(db_session, email="shortpw@example.com")
    db_session.flush()
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "shortpw@example.com", "password": PASSWORD}
    )
    access_token = login_resp.json()["access_token"]

    resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": PASSWORD, "new_password": "short"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 422
