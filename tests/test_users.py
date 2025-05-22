import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, get_password_hash
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.exceptions import AuthenticationException
from datetime import datetime
from app.services.user_service import UserService
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import selectinload

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def test_user_data():
    """Test user data."""
    return {
        "email": f"test_{uuid4()}@example.com",
        "username": f"testuser_{uuid4()}",
        "password": "testpass123",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False
    }

@pytest.fixture
async def test_user(session: AsyncSession, test_user_data):
    """Create a test user."""
    user = User(
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"]),
        full_name=test_user_data["full_name"],
        is_active=test_user_data["is_active"],
        is_superuser=test_user_data["is_superuser"]
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest.mark.asyncio
async def test_create_user(db: AsyncSession):
    service = UserService(db)
    user_data = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "testpass",
        "full_name": "New User",
        "is_active": True
    }
    user = await service.create_user(UserCreate(**user_data))
    
    assert user.email == user_data["email"]
    assert user.username == user_data["username"]
    assert user.full_name == user_data["full_name"]
    assert user.is_active == user_data["is_active"]

@pytest.mark.asyncio
async def test_get_user(db: AsyncSession, test_user):
    service = UserService(db)
    user = await service.get_user(test_user.id)
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email

@pytest.mark.asyncio
async def test_update_user(db: AsyncSession, test_user):
    service = UserService(db)
    update_data = UserUpdate(
        full_name="Updated Name",
        email="updated@example.com"
    )
    updated_user = await service.update_user(test_user.id, update_data)
    assert updated_user is not None
    assert updated_user.full_name == "Updated Name"
    assert updated_user.email == "updated@example.com"

@pytest.mark.asyncio
async def test_delete_user(db: AsyncSession, test_user):
    service = UserService(db)
    success = await service.delete_user(test_user.id)
    assert success is True
    
    deleted_user = await service.get_user(test_user.id)
    assert deleted_user is None

@pytest.mark.asyncio
async def test_user_authentication(client: AsyncClient, test_user_data: dict):
    """Test user authentication."""
    # Register user
    await client.post("/api/auth/register", json=test_user_data)
    
    # Login
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_response = await client.post("/api/auth/login", data=login_data)
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_user_validation(db: AsyncSession):
    service = UserService(db)
    invalid_data = {
        "email": "invalid-email",
        "username": "test",
        "password": "short"
    }
    with pytest.raises(ValueError):
        await service.create_user(UserCreate(**invalid_data))

@pytest.mark.asyncio
async def test_user_relationships(session: AsyncSession, test_user):
    """Test user relationships."""
    # Test user events relationship
    result = await session.execute(select(User).where(User.id == test_user.id).options(selectinload(User.created_events)))
    user = result.unique().scalar_one()
    assert user.created_events == []
    
    # Test user shares relationship
    result = await session.execute(select(User).where(User.id == test_user.id).options(selectinload(User.shared_events)))
    user = result.unique().scalar_one()
    assert user.shared_events == []
    
    # Test user notifications relationship
    result = await session.execute(select(User).where(User.id == test_user.id).options(selectinload(User.notifications)))
    user = result.unique().scalar_one()
    assert user.notifications == []

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, test_user_data: dict):
    """Test user registration."""
    response = await client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]
    assert data["full_name"] == test_user_data["full_name"]
    assert "id" in data

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user_data):
    # First registration
    await client.post("/api/auth/register", json=test_user_data)
    
    # Try to register again with same email
    response = await client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == 400
    assert "email already registered" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_user_data: dict):
    """Test getting current user information."""
    # Register and login
    await client.post("/api/auth/register", json=test_user_data)
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_response = await client.post("/api/auth/login", data=login_data)
    token = login_response.json()["access_token"]

    # Get current user
    response = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]

@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, test_user_data: dict):
    """Test updating user information."""
    # Register and login
    await client.post("/api/auth/register", json=test_user_data)
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_response = await client.post("/api/auth/login", data=login_data)
    token = login_response.json()["access_token"]

    # Update user
    update_data = {
        "full_name": "Updated Name",
        "password": "newpassword123"
    }
    response = await client.put(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_data["full_name"]

@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, test_user_data: dict):
    """Test deleting a user."""
    # Register and login
    await client.post("/api/auth/register", json=test_user_data)
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    login_response = await client.post("/api/auth/login", data=login_data)
    token = login_response.json()["access_token"]

    # Delete user
    response = await client.delete(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204

    # Verify user is deleted
    response = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401 