import os
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.core.config import settings
from app.core.models import Base
from app.db.session import get_db
from app.core.security.core_security import get_password_hash
from datetime import datetime, timedelta
import re
import uuid
from app.models.user import User, UserRole
from app.core.security_middleware import setup_middleware

# Create test database engine
TEST_DATABASE_URL = settings.TEST_DATABASE_URL
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,
    poolclass=StaticPool,
    connect_args={
        "command_timeout": settings.DB_COMMAND_TIMEOUT,
        "server_settings": {
            "application_name": f"{settings.PROJECT_NAME}_test",
            "statement_timeout": str(settings.DB_STATEMENT_TIMEOUT),
            "idle_in_transaction_session_timeout": str(settings.DB_IDLE_TIMEOUT)
        }
    }
)
TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    # Create test database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Clean up test database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def session(test_db) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@pytest.fixture
async def db(session) -> AsyncGenerator[AsyncSession, None]:
    """Alias for session fixture."""
    yield session

@pytest.fixture
async def client(session) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with a test database session."""
    async def override_get_db():
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpass"),
        full_name="Test User",
        role=UserRole.ADMIN,
        is_superuser=True,
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest.fixture
async def test_user_data() -> dict:
    """Test user data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": True
    }

@pytest.fixture
async def test_admin(session: AsyncSession) -> User:
    unique_id = str(uuid.uuid4())[:8]
    admin = User(
        id=str(uuid.uuid4()),
        email=f"admin_{unique_id}@example.com",
        username=f"admin_{unique_id}",
        full_name="Test Admin",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        role=UserRole.ADMIN
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin

@pytest.fixture
async def test_token(test_user):
    return get_password_hash(
        data={"sub": test_user.email},
        expires_delta=timedelta(minutes=15)
    )

@pytest.fixture
async def test_admin_token(test_admin):
    return get_password_hash(
        data={"sub": test_admin.email},
        expires_delta=timedelta(minutes=15)
    )

@pytest.fixture
async def auth_headers(test_token):
    return {"Authorization": f"Bearer {test_token}"}

@pytest.fixture
async def admin_headers(test_admin_token):
    return {"Authorization": f"Bearer {test_admin_token}"} 