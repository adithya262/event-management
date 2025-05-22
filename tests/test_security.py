import pytest
from datetime import datetime, timedelta
from jose import jwt
from app.core.security import (
    SecurityUtils,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    validate_password_strength
)
from app.core.config import settings
from app.core.exceptions import AuthenticationException
import time
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_password_hashing(session: AsyncSession):
    password = "testpassword123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)

@pytest.mark.asyncio
async def test_token_creation(session: AsyncSession):
    data = {"sub": "testuser"}
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    assert access_token is not None
    assert refresh_token is not None
    access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert access_payload["sub"] == "testuser"
    assert refresh_payload["sub"] == "testuser"
    assert "exp" in access_payload
    assert "exp" in refresh_payload

@pytest.mark.asyncio
async def test_token_verification(session: AsyncSession):
    data = {"sub": "testuser"}
    token = create_access_token(data)
    payload = verify_token(token)
    assert payload["sub"] == "testuser"
    assert "exp" in payload
    assert "iat" in payload

@pytest.mark.asyncio
async def test_token_expiration(session: AsyncSession):
    data = {"sub": "testuser"}
    token = create_access_token(data, expires_delta=timedelta(seconds=1))
    payload = verify_token(token)
    assert payload["sub"] == "testuser"
    time.sleep(2)
    with pytest.raises(AuthenticationException) as exc_info:
        verify_token(token)
    assert "Token has expired" in exc_info.value.detail

@pytest.mark.asyncio
async def test_password_strength_validation(session: AsyncSession):
    strong_password = "StrongP@ssw0rd123"
    assert validate_password_strength(strong_password)
    weak_passwords = [
        "short",
        "password",
        "12345678",
        "abcdefgh",
    ]
    for password in weak_passwords:
        assert not validate_password_strength(password)

@pytest.mark.asyncio
async def test_invalid_token(session: AsyncSession):
    with pytest.raises(AuthenticationException) as exc_info:
        verify_token("invalid.token.here")
    assert "Invalid token" in str(exc_info.value)
    data = {"sub": "testuser"}
    token = create_access_token(data)
    tampered_token = token[:-5] + "12345"
    with pytest.raises(AuthenticationException) as exc_info:
        verify_token(tampered_token)
    assert "Invalid token" in str(exc_info.value)

@pytest.mark.asyncio
async def test_token_scopes(session: AsyncSession):
    data = {"sub": "testuser"}
    scopes = ["user", "admin"]
    token = create_access_token(data, scopes=scopes)
    payload = verify_token(token)
    assert "scopes" in payload
    assert set(payload["scopes"]) == set(scopes)

@pytest.mark.asyncio
async def test_refresh_token(session: AsyncSession):
    data = {"sub": "testuser"}
    refresh_token = create_refresh_token(data)
    payload = verify_token(refresh_token)
    assert payload["sub"] == "testuser"
    assert payload["type"] == "refresh"
    access_token = create_access_token(data)
    access_payload = verify_token(access_token)
    refresh_payload = verify_token(refresh_token)
    assert refresh_payload["exp"] > access_payload["exp"] 