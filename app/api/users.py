from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID # Assuming UUID is used for user IDs

from app.db.session import get_db
from app.api.dependencies import get_current_user, check_permissions
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserInDB
from app.core.security.core_security import get_password_hash
from app.services.user_service import UserService

router = APIRouter()

@router.post("/", response_model=UserInDB)
async def create_user(
    user: UserCreate,
    current_user: User = Depends(check_permissions(UserRole.OWNER)), # Admin only
    db: AsyncSession = Depends(get_db)
) -> UserInDB:
    """Create a new user (Admin only)."""
    existing_user = await db.execute(
        select(User).where(User.email == user.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        role=user.role,
        full_name=user.full_name
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[UserInDB])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_permissions(UserRole.OWNER)), # Admin only
    db: AsyncSession = Depends(get_db)
) -> List[UserInDB]:
    """List all users."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users

@router.get("/me", response_model=UserInDB)
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> UserInDB:
    """Get current user information."""
    return current_user

@router.put("/me", response_model=UserInDB)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserInDB:
    """Update current user information."""
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        hashed_password = get_password_hash(update_data.pop("password"))
        update_data["hashed_password"] = hashed_password

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.get("/{user_id}", response_model=UserInDB)
async def read_user_by_id(
    user_id: UUID,
    current_user: User = Depends(check_permissions(UserRole.OWNER)), # Admin only
    db: AsyncSession = Depends(get_db)
) -> UserInDB:
    """Get user by ID (Admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserInDB)
async def update_user_by_id(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(check_permissions(UserRole.OWNER)), # Admin only
    db: AsyncSession = Depends(get_db)
) -> UserInDB:
    """Update user by ID (Admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        hashed_password = get_password_hash(update_data.pop("password"))
        update_data["hashed_password"] = hashed_password

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_id(
    user_id: UUID,
    current_user: User = Depends(check_permissions(UserRole.OWNER)), # Admin only
    db: AsyncSession = Depends(get_db)
):
    """Delete user by ID (Admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.delete(user)
    await db.commit()
    return 