from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError
from pydantic import ValidationError

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Use email from token subject
    result = await db.execute(select(User).where(User.email == token_data.sub))
    user = result.unique().scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def check_permissions(required_role: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_superuser and current_user.role.value < required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return dependency
