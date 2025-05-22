from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from datetime import datetime

from app.db.session import get_db
from app.core.security import (
    get_current_user,
    get_password_hash,
    create_access_token,
    verify_password
)
from app.models.user import User, UserRole # Assuming UserRole is needed here
from app.schemas.user import UserInDB, Token, UserRegister
from app.core.config import settings
from app.core.cache import TokenBlocklistManager

router = APIRouter()

@router.post("/register", response_model=UserInDB)
async def register_user(
    user: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    # Check if user with email already exists
    existing_user = await db.execute(
        select(User).where(User.email == user.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user with default role (e.g., UserRole.USER)
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        role=UserRole.USER,
        full_name=user.full_name
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
async def login_for_access_token(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """Get access token for user."""
    user = await db.execute(select(User).where(User.email == email))
    user = user.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """Refresh an authentication token."""
    # The get_current_user dependency already ensures the token is valid and not blocklisted.
    # We just need to create and return a new token for the authenticated user.
    new_access_token = create_access_token(data={"sub": str(current_user.id)})
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
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
            await TokenBlocklistManager.add_to_blocklist(jti, int(remaining_expires_in))

    except jwt.ExpiredSignatureError:
        pass
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return {"message": "Token invalidated successfully"} 