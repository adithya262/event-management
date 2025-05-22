import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from pydantic import ValidationError
from app.core.config import settings
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.models.user import User, UserRole
import logging

logger = logging.getLogger(__name__)

# Password hashing configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increased rounds for better security
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    scopes={
        "user": "User access",
        "admin": "Admin access",
        "editor": "Editor access"
    }
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

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
        "type": "access"
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
        if "expired" in str(e).lower():
            raise AuthenticationException(
                message="Token has expired",
                details={"error": str(e)}
            )
        raise AuthenticationException(
            message="Invalid token",
            details={"error": str(e)}
        )

async def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID."""
    from app.services.user_service import UserService
    from app.db.session import async_session
    async with async_session() as session:
        user_service = UserService(session)
        try:
            return await user_service.get_user(user_id)
        except Exception:
            return None

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get current user from token with scope validation."""
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise AuthenticationException(
                message="Invalid token payload",
                details={"error": "Missing user ID in token"}
            )

        # Verify token type
        token_type = payload.get("type")
        if token_type != "access":
            raise AuthenticationException(
                message="Invalid token type",
                details={"error": "Token must be an access token"}
            )

        # Verify scopes
        token_scopes = payload.get("scopes", [])
        for scope in security_scopes.scopes:
            if scope not in token_scopes:
                raise AuthorizationException(
                    message="Not enough permissions",
                    details={"required_scopes": security_scopes.scopes}
                )

        # Get user from database
        user = await get_user_by_id(user_id)
        if not user:
            raise AuthenticationException(
                message="User not found",
                details={"user_id": user_id}
            )

        return user

    except (JWTError, ValidationError) as e:
        logger.error(f"Token validation failed: {str(e)}")
        if "expired" in str(e).lower():
            raise AuthenticationException(
                message="Token has expired",
                details={"error": str(e)}
            )
        raise AuthenticationException(
            message="Could not validate credentials",
            details={"error": str(e)}
        )

def check_permissions(required_role: UserRole):
    """Check if user has required role."""
    async def permission_checker(
        current_user: User = Security(get_current_user, scopes=["user"])
    ) -> User:
        if current_user.role == UserRole.OWNER:
            return current_user
        if current_user.role == UserRole.EDITOR and required_role != UserRole.OWNER:
            return current_user
        if current_user.role == UserRole.VIEWER and required_role == UserRole.VIEWER:
            return current_user
        raise AuthorizationException(
            message="Not enough permissions",
            details={"required_role": required_role.value}
        )
    return permission_checker

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
