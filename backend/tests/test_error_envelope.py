"""section 5: every error response is {"error": {"code": "...", "message":
"..."}} — code a stable English string, message localized. Every existing
test so far only asserted status codes, never this envelope shape, so this
is the first real check of it."""


def test_error_response_has_code_and_localized_message(client, db_session):
    resp = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever123"}
    )
    assert resp.status_code == 401
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "invalid_credentials"
    assert isinstance(body["error"]["message"], str)
    assert body["error"]["message"]  # non-empty


def test_error_message_is_arabic_by_default(client, db_session):
    resp = client.get("/api/v1/auth/me")  # no Authorization header
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "unauthorized"
    # Arabic script range check — avoids hardcoding the exact sentence.
    assert any("؀" <= ch <= "ۿ" for ch in body["error"]["message"])


def test_error_message_is_localized_via_accept_language_french(client, db_session):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody2@example.com", "password": "whatever123"},
        headers={"Accept-Language": "fr"},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "invalid_credentials"
    assert "incorrect" in body["error"]["message"].lower()


def test_error_code_matches_the_specific_failure_not_a_generic_one(client, db_session):
    from app.core.security import hash_password
    from app.models.enums import UserRole
    from app.models.user import User

    user = User(
        full_name="Inactive",
        email="inactive-envelope@example.com",
        password_hash=hash_password("x" * 10),
        role=UserRole.MOQADDEM,
        is_active=False,
    )
    db_session.add(user)
    db_session.flush()

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive-envelope@example.com", "password": "x" * 10},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "account_inactive"
