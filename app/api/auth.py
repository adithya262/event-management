from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.db.session import get_db
from app.core.security import (
    get_password_hash,
    create_access_token,
    verify_password,
    create_refresh_token
)
from app.models.user import User, UserRole # Assuming UserRole is needed here for registration
from app.schemas.user import UserInDB, Token, UserRegister, UserCreate
from app.core.config import settings
from app.core.cache import TokenBlocklistManager # Assuming TokenBlocklistManager is used for logout
from app.api.dependencies import get_db, get_current_user # Import dependencies from the new location
from app.services.user_service import UserService

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register", response_model=Token)
async def register_user(
    user: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    user_service = UserService(db)
    try:
        db_user = await user_service.create_user(user)
        
        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(db_user.id)},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(db_user.id)}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Optional[OAuth2PasswordRequestForm] = Depends(),
    login_data: Optional[LoginRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """Login user and return access token."""
    user_service = UserService(db)
    try:
        # Handle both form data and direct JSON data
        if form_data:
            username = form_data.username
            password = form_data.password
        elif login_data:
            username = login_data.username
            password = login_data.password
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No login data provided"
            )

        user = await user_service.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token and get user
        user_service = UserService(db)
        user = await user_service.get_user_by_token(refresh_token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        # Create new refresh token
        new_refresh_token = create_refresh_token(
            data={"sub": user.email}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout_user(
    request: Request,
    db: AsyncSession = Depends(get_db) # Assuming db is needed for blocklist
):
    """Invalidate the current token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing or invalid")

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        jti: str = payload.get("jti")
        exp: int = payload.get("exp")

        if jti is None or exp is None:
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token does not contain required claims")

        expire_datetime = datetime.utcfromtimestamp(exp)
        remaining_expires_in = (expire_datetime - datetime.utcnow()).total_seconds()

        if remaining_expires_in > 0:
            # Assuming TokenBlocklistManager is accessible and has an add_to_blocklist method
            await TokenBlocklistManager.add_to_blocklist(jti, int(remaining_expires_in))

    except jwt.ExpiredSignatureError:
        pass # Token is already expired, consider it logged out
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return {"message": "Token invalidated successfully"} 