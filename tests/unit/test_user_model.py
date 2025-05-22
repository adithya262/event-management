import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.core.models import UserRole

@pytest.mark.asyncio
async def test_create_user(session):
    """Test creating a new user."""
    user = User(
        email="user1@example.com",
        username="user1",
        hashed_password="hashedpass",
        role=UserRole.VIEWER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    assert user.id is not None
    assert user.email == "user1@example.com"
    assert user.username == "user1"
    assert user.role == UserRole.VIEWER
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.disabled is False

@pytest.mark.asyncio
async def test_user_unique_constraints(session):
    """Test that unique constraints work correctly."""
    # Create first user
    user1 = User(
        email="unique1@example.com",
        username="uniqueuser1",
        hashed_password="hashedpass",
        role=UserRole.VIEWER
    )
    session.add(user1)
    await session.commit()

    # Try to create second user with same email
    user2 = User(
        email="unique1@example.com",  # Same email as user1
        username="uniqueuser2",
        hashed_password="hashedpass",
        role=UserRole.VIEWER
    )
    session.add(user2)
    with pytest.raises(Exception):  # Should raise an integrity error
        await session.commit()
    await session.rollback()

    # Try to create second user with same username
    user3 = User(
        email="unique2@example.com",
        username="uniqueuser1",  # Same username as user1
        hashed_password="hashedpass",
        role=UserRole.VIEWER
    )
    session.add(user3)
    with pytest.raises(Exception):  # Should raise an integrity error
        await session.commit()
    await session.rollback()

@pytest.mark.asyncio
async def test_user_relationships(session):
    """Test user relationships."""
    # Create a user
    user = User(
        email="user5@example.com",
        username="user5",
        hashed_password="hashedpass",
        role=UserRole.VIEWER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Eagerly load all relationships
    result = await session.execute(
        select(User)
        .options(
            selectinload(User.created_events),
            selectinload(User.events),
            selectinload(User.event_participations),
            selectinload(User.notifications),
            selectinload(User.event_shares),
            selectinload(User.created_versions),
            selectinload(User.created_event_versions),
        )
        .where(User.id == user.id)
    )
    loaded_user = result.unique().scalar_one()

    # Verify relationships are loaded
    assert loaded_user is not None
    assert loaded_user.email == user.email
    assert loaded_user.created_events is not None
    assert loaded_user.events is not None
    assert loaded_user.event_participations is not None
    assert loaded_user.notifications is not None
    assert loaded_user.event_shares is not None
    assert loaded_user.created_versions is not None
    assert loaded_user.created_event_versions is not None

@pytest.mark.asyncio
async def test_user_role_enum(session):
    """Test that user roles work correctly."""
    # Create users with different roles
    viewer = User(
        email="viewer@example.com",
        username="viewer",
        hashed_password="hashedpass",
        role=UserRole.VIEWER
    )
    editor = User(
        email="editor@example.com",
        username="editor",
        hashed_password="hashedpass",
        role=UserRole.EDITOR
    )
    owner = User(
        email="owner@example.com",
        username="owner",
        hashed_password="hashedpass",
        role=UserRole.OWNER
    )

    session.add_all([viewer, editor, owner])
    await session.commit()

    # Check that roles were set correctly
    assert viewer.role == UserRole.VIEWER
    assert editor.role == UserRole.EDITOR
    assert owner.role == UserRole.OWNER

    # Test role comparison
    assert viewer.role.value == "viewer"
    assert editor.role.value == "editor"
    assert owner.role.value == "owner"

@pytest.mark.asyncio
async def test_user_to_dict(session):
    """Test user serialization."""
    user = User(
        email="user6@example.com",
        username="user6",
        hashed_password="hashedpass",
        full_name="Test User",
        role=UserRole.VIEWER,
        is_superuser=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    user_dict = user.to_dict()
    assert isinstance(user_dict, dict)
    assert user_dict["email"] == "user6@example.com"
    assert user_dict["username"] == "user6"
    assert user_dict["full_name"] == "Test User"
    assert user_dict["role"] == UserRole.VIEWER.value
    assert user_dict["is_superuser"] is True
    assert user_dict["disabled"] is False
    assert "created_at" in user_dict
    assert "updated_at" in user_dict
    assert "id" in user_dict 