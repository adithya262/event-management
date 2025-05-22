from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.api.v1.dependencies import get_current_active_user, get_db
from app.core.security.roles import owner_required, editor_required, viewer_required
from app.models.user import User, UserRole
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate, UserInDB
from app.core.security import check_permissions, get_current_user
from app.services.user_service import UserService

router = APIRouter()

@router.get("/", response_model=List[UserSchema])
async def list_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_permissions(UserRole.OWNER)),
):
    """List all users (Admin only)."""
    service = UserService(db)
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users

@router.post("/", response_model=UserSchema)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(UserRole.OWNER)),
):
    """Create a new user (Admin only)."""
    service = UserService(db)
    try:
        return await service.create_user(user)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get("/me", response_model=UserSchema)
async def read_user_me(
    current_user: User = Depends(get_current_user),
):
    """Get current user information."""
    return current_user

@router.put("/me", response_model=UserSchema)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user information."""
    service = UserService(db)
    try:
        return await service.update_user(current_user.id, user_update)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=UserSchema)
async def read_user(
    user_id: UUID,
    current_user: User = Depends(check_permissions(UserRole.VIEWER)),
    db: AsyncSession = Depends(get_db),
):
    """Get user by ID."""
    service = UserService(db)
    try:
        user = await service.get_user(user_id)
        if user == current_user:
            return user
        if not current_user or not check_permissions(UserRole.OWNER)(current_user):
            raise HTTPException(
                status_code=400,
                detail="The user doesn't have enough privileges"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@router.put("/{user_id}", response_model=UserSchema)
async def update_user_by_id(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(check_permissions(UserRole.EDITOR)),
    db: AsyncSession = Depends(get_db),
):
    """Update user by ID (Admin only)."""
    service = UserService(db)
    try:
        return await service.update_user(user_id, user_update)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@router.delete("/{user_id}", response_model=UserSchema)
async def delete_user_by_id(
    user_id: UUID,
    current_user: User = Depends(check_permissions(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    """Delete user by ID (Admin only)."""
    service = UserService(db)
    try:
        success = await service.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
