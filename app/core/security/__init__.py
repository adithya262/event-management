# This file makes the security directory a Python package 

from app.core.security.core_security import (
    create_access_token,
    verify_password,
    get_password_hash,
    verify_token,
    get_current_user,
    check_permissions,
    validate_password_strength
)

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
from app.core.exceptions import AuthenticationException
import logging
import uuid

logger = logging.getLogger(__name__)

# Password hashing configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increased rounds for better security
)

class SecurityUtils:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
        scopes: Optional[list[str]] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({
            "exp": expire,
            "scopes": scopes or ["user"],
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": str(uuid.uuid4())
        })
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                settings.SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}")
            raise AuthenticationException(
                message="Error creating access token",
                details={"error": str(e)}
            )

    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
        
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow()
        })
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                settings.SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating refresh token: {str(e)}")
            raise AuthenticationException(
                message="Error creating refresh token",
                details={"error": str(e)}
            )

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.error(f"JWT verification failed: {str(e)}")
            raise AuthenticationException(
                message="Invalid token",
                details={"error": str(e)}
            )

def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT refresh token (module-level function for compatibility)."""
    return SecurityUtils.create_refresh_token(data, expires_delta)

def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload (module-level function for compatibility)."""
    return SecurityUtils.verify_token(token)

def validate_password_strength(password: str) -> bool:
    """Validate password strength."""
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False
    return True

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    scopes: Optional[list[str]] = None
) -> str:
    """Create JWT access token (module-level function for compatibility)."""
    return SecurityUtils.create_access_token(data, expires_delta, scopes)

__all__ = [
    "create_access_token",
    "verify_password",
    "get_password_hash",
    "verify_token",
    "get_current_user",
    "check_permissions",
    "validate_password_strength"
] 