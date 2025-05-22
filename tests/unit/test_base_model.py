import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.models import Base
from app.models.user import User
from app.models.event import Event
from app.core.models import UserRole

@pytest.mark.asyncio
async def test_base_model_fields(session):
    """Test that all models inherit base fields correctly."""
    # Create a test user
    user = User(
        email="test1@example.com",
        username="testuser1",
        hashed_password="hashedpass",
        role=UserRole.VIEWER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Check base fields
    assert user.id is not None
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)
    assert user.is_active is True

@pytest.mark.asyncio
async def test_base_model_timestamps(session):
    """Test that timestamps are updated correctly."""
    # Create a test user
    user = User(
        email="test2@example.com",
        username="testuser2",
        hashed_password="hashedpass",
        role=UserRole.VIEWER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Store initial timestamps
    initial_created_at = user.created_at
    initial_updated_at = user.updated_at

    # Update the user
    user.full_name = "Updated Name"
    await session.commit()
    await session.refresh(user)

    # Check that timestamps were updated correctly
    assert user.created_at == initial_created_at  # created_at should not change
    assert user.updated_at > initial_updated_at  # updated_at should be newer

@pytest.mark.asyncio
async def test_base_model_is_active(session):
    """Test that is_active field works correctly."""
    # Create a test user
    user = User(
        email="test3@example.com",
        username="testuser3",
        hashed_password="hashedpass",
        role=UserRole.VIEWER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Check initial state
    assert user.is_active is True

    # Deactivate the user
    user.is_active = False
    await session.commit()
    await session.refresh(user)

    # Check that is_active was updated
    assert user.is_active is False

@pytest.mark.asyncio
async def test_base_model_to_dict(session):
    """Test to_dict method of base model."""
    # Create a user
    user = User(
        email="user7@example.com",
        username="user7",
        hashed_password="hashedpass",
        role=UserRole.VIEWER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Create an event
    event = Event(
        title="Test Event",
        description="Test Description",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=1),
        created_by=user.id
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)

    # Eagerly load the participants relationship
    result = await session.execute(
        select(Event)
        .options(selectinload(Event.participants))
        .where(Event.id == event.id)
    )
    loaded_event = result.scalar_one()

    # Call to_dict on the loaded event
    event_dict = loaded_event.to_dict()
    assert isinstance(event_dict, dict)
    assert event_dict["title"] == "Test Event"
    assert event_dict["description"] == "Test Description"
    assert "start_time" in event_dict
    assert "end_time" in event_dict
    assert event_dict["created_by"] == user.id
    assert "participant_count" in event_dict 