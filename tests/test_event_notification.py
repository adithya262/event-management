import pytest
from datetime import datetime, timedelta
from app.services.event_notification import EventNotificationService
from app.models.event import Event, EventStatus
from app.models.event_share import EventShare, SharePermission
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.core.security.core_security import get_password_hash
from app.models.notification import Notification
from app.core.models import UserRole

@pytest.fixture
async def test_user(session: AsyncSession):
    """Create a test user for notifications."""
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        id=str(uuid.uuid4()),
        email=f"test_{unique_id}@example.com",
        username=f"testuser_{unique_id}",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        role=UserRole.USER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest.fixture
async def test_event(session: AsyncSession, test_user):
    """Create a test event."""
    event = Event(
        id=str(uuid.uuid4()),
        title="Test Event",
        description="Test event description",
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=2),
        location="Test Location",
        created_by=test_user.id,
        owner_id=test_user.id,
        max_participants=10,
        is_active=True
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event

@pytest.mark.asyncio
async def test_notify_event_created(session: AsyncSession, test_user, test_event):
    """Test notification for event creation."""
    service = EventNotificationService(session)
    notification = await service.notify_event_created(test_event)
    
    assert notification is not None
    assert notification.user_id == test_user.id
    assert notification.event_id == test_event.id
    assert notification.type == "event_created"
    assert notification.is_read == False

@pytest.mark.asyncio
async def test_notify_event_updated(session: AsyncSession, test_user, test_event):
    """Test notification for event update."""
    service = EventNotificationService(session)
    notification = await service.notify_event_updated(test_event)
    
    assert notification is not None
    assert notification.user_id == test_user.id
    assert notification.event_id == test_event.id
    assert notification.type == "event_updated"
    assert notification.is_read == False

@pytest.mark.asyncio
async def test_notify_event_deleted(session: AsyncSession, test_user, test_event):
    """Test notification for event deletion."""
    service = EventNotificationService(session)
    notification = await service.notify_event_deleted(test_event)
    
    assert notification is not None
    assert notification.user_id == test_user.id
    assert notification.event_id == test_event.id
    assert notification.type == "event_deleted"
    assert notification.is_read == False

@pytest.mark.asyncio
async def test_notify_event_reminder(session: AsyncSession, test_user, test_event):
    """Test notification for event reminder."""
    service = EventNotificationService(session)
    notification = await service.notify_event_reminder(test_event)
    
    assert notification is not None
    assert notification.user_id == test_user.id
    assert notification.event_id == test_event.id
    assert notification.type == "event_reminder"
    assert notification.is_read == False

@pytest.mark.asyncio
async def test_notify_participant_joined(session: AsyncSession, test_user, test_event):
    """Test notification for participant joining."""
    service = EventNotificationService(session)
    notification = await service.notify_participant_joined(test_event, test_user)
    
    assert notification is not None
    assert notification.user_id == test_user.id
    assert notification.event_id == test_event.id
    assert notification.type == "participant_joined"
    assert notification.is_read == False

@pytest.mark.asyncio
async def test_notify_participant_left(session: AsyncSession, test_user, test_event):
    """Test notification for participant leaving."""
    service = EventNotificationService(session)
    notification = await service.notify_participant_left(test_event, test_user)
    
    assert notification is not None
    assert notification.user_id == test_user.id
    assert notification.event_id == test_event.id
    assert notification.type == "participant_left"
    assert notification.is_read == False

@pytest.mark.asyncio
async def test_notify_event_conflict(session: AsyncSession, test_user, test_event):
    """Test notification for event conflict."""
    service = EventNotificationService(session)
    notification = await service.notify_event_conflict(test_event)
    
    assert notification is not None
    assert notification.user_id == test_user.id
    assert notification.event_id == test_event.id
    assert notification.type == "event_conflict"
    assert notification.is_read == False 