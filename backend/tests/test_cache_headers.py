from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User

PASSWORD = "correct horse battery staple"


def test_api_responses_are_never_cached(client):
    """Regression test: found live via the browser — a GET response with
    no Cache-Control header is heuristically cacheable by URL alone (a
    cache never varies by Authorization unless told to), so one user's
    cached response can be served back to a completely different signed
    -in user who later requests the identical URL. Every route here is
    per-user/territory-scoped, so none of them may ever be cached."""
    response = client.get("/api/v1/health")
    assert response.headers["cache-control"] == "no-store"


def test_authenticated_endpoint_is_also_never_cached(client, db_session):
    user = User(
        full_name="Admin",
        email="cache-test-admin@example.com",
        password_hash=hash_password(PASSWORD),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.flush()
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "cache-test-admin@example.com", "password": PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.get("/api/v1/users", headers=headers)

    assert response.headers["cache-control"] == "no-store"
