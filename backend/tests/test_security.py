from uuid import uuid4

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    password = "correct-horse-battery-staple"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_token_hash_is_deterministic_and_not_plaintext() -> None:
    token = "refresh-token-value"
    hashed = hash_token(token)

    assert hashed != token
    assert hash_token(token) == hashed


def test_access_token_contains_session_claims() -> None:
    user_id = str(uuid4())
    session_id = uuid4()
    token = create_access_token(user_id, session_id)

    claims = decode_token(token)
    assert claims["sub"] == user_id
    assert claims["sid"] == str(session_id)
    assert claims["type"] == "access"
    assert claims["jti"]


def test_refresh_token_contains_session_claims_and_expiry() -> None:
    user_id = str(uuid4())
    session_id = uuid4()
    token, expires_at = create_refresh_token(user_id, session_id)

    claims = decode_token(token)
    assert claims["sub"] == user_id
    assert claims["sid"] == str(session_id)
    assert claims["type"] == "refresh"
    assert claims["jti"]
    assert expires_at.isoformat().startswith("20")
