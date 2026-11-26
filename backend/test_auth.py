from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_password_hashing():
    password = "TestPassword123"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)


def test_wrong_password():
    hashed = hash_password("TestPassword123")

    assert not verify_password("WrongPassword", hashed)


def test_create_and_decode_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-" * 3)

    token = create_access_token(1, "owner")
    payload = decode_access_token(token)

    assert payload["sub"] == "1"
    assert payload["role"] == "owner"


def test_invalid_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-" * 3)

    assert decode_access_token("invalid-token") is None
import pytest
from fastapi import HTTPException
from backend.auth import require_owner


def test_owner_access():
    user = {"sub": "1", "role": "owner"}
    assert require_owner(user) == user


def test_staff_access_denied():
    user = {"sub": "2", "role": "staff"}

    with pytest.raises(HTTPException) as exc:
        require_owner(user)

    assert exc.value.status_code == 403