import time

import jwt as pyjwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    is_password_strong_enough,
    verify_password,
)


def test_hash_password_is_not_the_plaintext():
    hashed = hash_password("correct horse battery")
    assert hashed != "correct horse battery"
    assert hashed.startswith("$argon2id$")


def test_verify_password_accepts_correct_password():
    hashed = hash_password("correct horse battery")
    assert verify_password("correct horse battery", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("correct horse battery")
    assert verify_password("wrong password", hashed) is False


@pytest.mark.parametrize(
    "password,expected",
    [
        ("short", False),
        ("exactly10c", True),
        ("a very long and strong password", True),
        ("", False),
    ],
)
def test_password_strength_minimum_10_chars(password, expected):
    assert is_password_strong_enough(password) is expected


def test_create_access_token_contains_required_claims():
    token = create_access_token(
        subject="user-123", role="manager", secret="s3cret", expire_minutes=15
    )
    decoded = pyjwt.decode(token, "s3cret", algorithms=["HS256"])
    assert decoded["sub"] == "user-123"
    assert decoded["role"] == "manager"
    assert "exp" in decoded
    assert "jti" in decoded


def test_decode_access_token_round_trips():
    token = create_access_token(
        subject="user-123", role="manager", secret="s3cret", expire_minutes=15
    )
    decoded = decode_access_token(token, "s3cret")
    assert decoded["sub"] == "user-123"
    assert decoded["role"] == "manager"


def test_decode_access_token_rejects_wrong_secret():
    token = create_access_token(
        subject="user-123", role="manager", secret="s3cret", expire_minutes=15
    )
    with pytest.raises(pyjwt.InvalidTokenError):
        decode_access_token(token, "wrong-secret")


def test_decode_access_token_rejects_expired_token():
    token = create_access_token(
        subject="user-123", role="manager", secret="s3cret", expire_minutes=-1
    )
    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_access_token(token, "s3cret")


def test_two_access_tokens_have_different_jti():
    t1 = create_access_token(subject="u", role="admin", secret="s", expire_minutes=15)
    t2 = create_access_token(subject="u", role="admin", secret="s", expire_minutes=15)
    d1 = decode_access_token(t1, "s")
    d2 = decode_access_token(t2, "s")
    assert d1["jti"] != d2["jti"]


def test_generate_refresh_token_is_random_and_long():
    t1 = generate_refresh_token()
    t2 = generate_refresh_token()
    assert t1 != t2
    assert len(t1) >= 32


def test_hash_refresh_token_is_deterministic_sha256():
    token = "some-opaque-token"
    h1 = hash_refresh_token(token)
    h2 = hash_refresh_token(token)
    assert h1 == h2
    assert len(h1) == 64  # sha256 hex digest length
    assert h1 != token
