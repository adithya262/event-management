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
    """Test password hashing and verification."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    # Verify password hash
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)

@pytest.mark.asyncio
async def test_token_creation(session: AsyncSession):
    """Test JWT token creation."""
    data = {"sub": "testuser"}
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    
    # Verify tokens are created
    assert access_token is not None
    assert refresh_token is not None
    
    # Verify token structure
    access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    assert access_payload["sub"] == "testuser"
    assert refresh_payload["sub"] == "testuser"
    assert "exp" in access_payload
    assert "exp" in refresh_payload

@pytest.mark.asyncio
async def test_token_verification(session: AsyncSession):
    """Test JWT token verification."""
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    # Verify token
    payload = verify_token(token)
    assert payload["sub"] == "testuser"
    assert "exp" in payload
    assert "iat" in payload

@pytest.mark.asyncio
async def test_token_expiration(session: AsyncSession):
    """Test token expiration."""
    data = {"sub": "testuser"}
    # Create token with 1 second expiration
    token = create_access_token(data, expires_delta=timedelta(seconds=1))
    
    # Verify token is valid initially
    payload = verify_token(token)
    assert payload["sub"] == "testuser"
    
    # Wait for token to expire
    time.sleep(2)
    
    # Verify token is expired
    with pytest.raises(AuthenticationException) as exc_info:
        verify_token(token)
    assert "Token has expired" in exc_info.value.detail

@pytest.mark.asyncio
async def test_password_strength_validation(session: AsyncSession):
    """Test password strength validation."""
    # Test strong password
    strong_password = "StrongP@ssw0rd123"
    assert validate_password_strength(strong_password)
    
    # Test weak passwords
    weak_passwords = [
        "short",  # Too short
        "password",  # No numbers or special chars
        "12345678",  # No letters
        "abcdefgh",  # No numbers or special chars
    ]
    
    for password in weak_passwords:
        assert not validate_password_strength(password)

@pytest.mark.asyncio
async def test_invalid_token(session: AsyncSession):
    """Test invalid token handling."""
    # Test with invalid token
    with pytest.raises(AuthenticationException) as exc_info:
        verify_token("invalid.token.here")
    assert "Invalid token" in str(exc_info.value)
    
    # Test with tampered token
    data = {"sub": "testuser"}
    token = create_access_token(data)
    tampered_token = token[:-5] + "12345"  # Tamper with the signature
    
    with pytest.raises(AuthenticationException) as exc_info:
        verify_token(tampered_token)
    assert "Invalid token" in str(exc_info.value)

@pytest.mark.asyncio
async def test_token_scopes(session: AsyncSession):
    """Test token scope validation."""
    data = {"sub": "testuser"}
    scopes = ["user", "admin"]
    token = create_access_token(data, scopes=scopes)
    
    # Verify token scopes
    payload = verify_token(token)
    assert "scopes" in payload
    assert set(payload["scopes"]) == set(scopes)

@pytest.mark.asyncio
async def test_refresh_token(session: AsyncSession):
    """Test refresh token functionality."""
    data = {"sub": "testuser"}
    refresh_token = create_refresh_token(data)
    
    # Verify refresh token
    payload = verify_token(refresh_token)
    assert payload["sub"] == "testuser"
    assert payload["type"] == "refresh"
    
    # Verify refresh token has longer expiration
    access_token = create_access_token(data)
    access_payload = verify_token(access_token)
    refresh_payload = verify_token(refresh_token)
    assert refresh_payload["exp"] > access_payload["exp"] 