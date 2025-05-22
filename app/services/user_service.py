from typing import Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.security.core_security import get_password_hash, verify_password, verify_token
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserRegister
from app.core.exceptions import NotFoundException, ValidationException
from app.core.models import UserRole

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user: Union[UserCreate, UserRegister]) -> User:
        """Create a new user."""
        # Check if user with email already exists
        result = await self.db.execute(
            select(User).where(User.email == user.email)
        )
        existing_user = result.unique().scalar_one_or_none()
        if existing_user:
            raise ValidationException("Email already registered")

        # Create new user
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            full_name=user.full_name,
            is_active=user.is_active if hasattr(user, "is_active") else True,
            is_superuser=user.is_superuser if hasattr(user, "is_superuser") else False,
            role=user.role if hasattr(user, "role") else UserRole.VIEWER
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def get_user(self, user_id: Union[int, str, UUID]) -> User:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.unique().scalar_one_or_none()
        if not user:
            raise NotFoundException("User not found")
        return user

    async def get_user_by_email(self, email: str) -> User:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.unique().scalar_one_or_none()
        if not user:
            raise NotFoundException("User not found")
        return user

    async def get_user_by_token(self, token: str) -> User:
        """Get user from token."""
        try:
            payload = verify_token(token)
            if payload.get("type") != "refresh":
                raise ValidationException("Invalid token type")
            user_id = payload.get("sub")
            if not user_id:
                raise ValidationException("Invalid token")
            return await self.get_user(user_id)
        except Exception as e:
            raise ValidationException("Invalid token")

    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user with email and password."""
        try:
            user = await self.get_user_by_email(email)
            if not verify_password(password, user.hashed_password):
                raise ValidationException("Incorrect password")
            if not user.is_active:
                raise ValidationException("User is inactive")
            return user
        except NotFoundException:
            # Don't reveal whether the email exists or not
            raise ValidationException("Incorrect email or password")
        except Exception as e:
            raise ValidationException(str(e))

    async def update_user(self, user_id: Union[int, str, UUID], user_update: UserCreate) -> User:
        """Update user information."""
        user = await self.get_user(user_id)
        
        # Update fields
        for field, value in user_update.dict(exclude_unset=True).items():
            if field == "password":
                value = get_password_hash(value)
            setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: Union[int, str, UUID]) -> None:
        """Delete a user."""
        user = await self.get_user(user_id)
        await self.db.delete(user)
        await self.db.commit()

    async def verify_password(self, user_id: Union[int, str, UUID], password: str) -> bool:
        user = await self.get_user(user_id)
        return verify_password(password, user.hashed_password)

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()
