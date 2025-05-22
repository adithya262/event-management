import pytest
from datetime import datetime, timedelta
from app.services.event import EventService
from app.models.event import Event, EventStatus, RecurrencePattern
from app.models.event_share import EventShare, SharePermission
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.core.security.core_security import get_password_hash
from app.models.user import User
from app.core.models import UserRole

@pytest.fixture
async def test_user(session: AsyncSession):
    """Create a test user for events."""
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
        max_participants=10,
        is_active=True
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event

@pytest.fixture
def sample_event_data(test_user):
    return {
        "title": "Test Event",
        "start_time": datetime.now() + timedelta(days=1),
        "end_time": datetime.now() + timedelta(days=1, hours=2),
        "description": "Test Description",
        "location": "Test Location",
        "max_participants": 10,
        "is_private": False,
        "created_by": test_user.id
    }

@pytest.fixture
def sample_recurring_event_data():
    """Create sample recurring event data for testing."""
    return {
        "title": "Recurring Event",
        "start_time": datetime.now() + timedelta(days=1),
        "end_time": datetime.now() + timedelta(days=1, hours=2),
        "description": "Recurring Description",
        "location": "Recurring Location",
        "max_participants": 5,
        "is_private": True,
        "recurrence_pattern": RecurrencePattern.WEEKLY,
        "recurrence_end_date": datetime.now() + timedelta(days=30),
        "recurrence_interval": 2,
        "recurrence_days": ["Monday", "Wednesday", "Friday"]
    }

@pytest.mark.asyncio
async def test_create_event(session: AsyncSession, test_user):
    """Test event creation."""
    service = EventService(session)
    event_data = {
        "title": "New Event",
        "description": "New event description",
        "start_time": datetime.now() + timedelta(days=1),
        "end_time": datetime.now() + timedelta(days=1, hours=2),
        "location": "New Location",
        "max_participants": 20,
        "created_by": test_user.id
    }
    
    event, instances = await service.create_event(**event_data)
    
    assert event is not None
    assert event.title == event_data["title"]
    assert event.description == event_data["description"]
    assert event.created_by == test_user.id
    assert event.is_active == True
    assert len(instances) == 0  # No recurring instances

@pytest.mark.asyncio
async def test_get_event(session: AsyncSession, test_user):
    """Test getting an event."""
    service = EventService(session)
    event_data = {
        "title": "Test Event",
        "description": "Test event description",
        "start_time": datetime.now() + timedelta(days=1),
        "end_time": datetime.now() + timedelta(days=1, hours=2),
        "location": "Test Location",
        "max_participants": 10,
        "created_by": test_user.id
    }
    
    event, _ = await service.create_event(**event_data)
    retrieved_event = await service.get_event(event.id, test_user.id)
    
    assert retrieved_event is not None
    assert retrieved_event.id == event.id
    assert retrieved_event.title == event_data["title"]

@pytest.mark.asyncio
async def test_update_event(session: AsyncSession, test_user):
    """Test updating an event."""
    service = EventService(session)
    event_data = {
        "title": "Test Event",
        "description": "Test event description",
        "start_time": datetime.now() + timedelta(days=1),
        "end_time": datetime.now() + timedelta(days=1, hours=2),
        "location": "Test Location",
        "max_participants": 10,
        "created_by": test_user.id
    }
    
    event, _ = await service.create_event(**event_data)
    updates = {
        "title": "Updated Event",
        "description": "Updated description"
    }
    
    updated_event = await service.update_event(event.id, updates, test_user.id)
    
    assert updated_event is not None
    assert updated_event.title == updates["title"]
    assert updated_event.description == updates["description"]

@pytest.mark.asyncio
async def test_delete_event(session: AsyncSession, test_user):
    """Test deleting an event."""
    service = EventService(session)
    event_data = {
        "title": "Test Event",
        "description": "Test event description",
        "start_time": datetime.now() + timedelta(days=1),
        "end_time": datetime.now() + timedelta(days=1, hours=2),
        "location": "Test Location",
        "max_participants": 10,
        "created_by": test_user.id
    }
    
    event, _ = await service.create_event(**event_data)
    result = await service.delete_event(event.id, test_user.id)
    
    assert result is True
    deleted_event = await service.get_event(event.id, test_user.id)
    assert deleted_event is None

@pytest.mark.asyncio
async def test_list_events(session: AsyncSession, test_user):
    """Test listing events."""
    service = EventService(session)
    
    # Create multiple events
    for i in range(3):
        event_data = {
            "title": f"Event {i}",
            "description": f"Description {i}",
            "start_time": datetime.now() + timedelta(days=i),
            "end_time": datetime.now() + timedelta(days=i, hours=2),
            "location": f"Location {i}",
            "max_participants": 10,
            "created_by": test_user.id
        }
        await service.create_event(**event_data)
    
    events = await service.list_events(user_id=test_user.id)
    assert len(events) >= 3

@pytest.mark.asyncio
async def test_add_participant(session: AsyncSession, test_event, test_user):
    """Test adding a participant to an event."""
    service = EventService(session)
    
    # Create another user to add as participant
    participant = User(
        id=str(uuid.uuid4()),
        email=f"participant_{uuid.uuid4()}@example.com",
        username=f"participant_{uuid.uuid4()}",
        full_name="Test Participant",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        role="user"
    )
    session.add(participant)
    await session.commit()
    
    await service.add_participant(test_event.id, participant.id)
    
    event = await service.get_event(test_event.id)
    assert participant.id in [p.id for p in event.participants]

@pytest.mark.asyncio
async def test_remove_participant(session: AsyncSession, test_event, test_user):
    """Test removing a participant from an event."""
    service = EventService(session)
    
    # Create another user to add as participant
    participant = User(
        id=str(uuid.uuid4()),
        email=f"participant_{uuid.uuid4()}@example.com",
        username=f"participant_{uuid.uuid4()}",
        full_name="Test Participant",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        role="user"
    )
    session.add(participant)
    await session.commit()
    
    # Add participant first
    await service.add_participant(test_event.id, participant.id)
    
    # Then remove them
    await service.remove_participant(test_event.id, participant.id)
    
    event = await service.get_event(test_event.id)
    assert participant.id not in [p.id for p in event.participants]

@pytest.mark.asyncio
async def test_check_event_conflicts(session: AsyncSession, test_user):
    """Test checking for event conflicts."""
    service = EventService(session)
    
    # Create an event
    event1 = Event(
        id=str(uuid.uuid4()),
        title="Event 1",
        description="Description 1",
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=2),
        location="Location 1",
        created_by=test_user.id,
        max_participants=10,
        is_active=True
    )
    session.add(event1)
    await session.commit()
    
    # Create a conflicting event
    event2 = Event(
        id=str(uuid.uuid4()),
        title="Event 2",
        description="Description 2",
        start_time=datetime.now() + timedelta(days=1, hours=1),  # Overlaps with event1
        end_time=datetime.now() + timedelta(days=1, hours=3),
        location="Location 2",
        created_by=test_user.id,
        max_participants=10,
        is_active=True
    )
    session.add(event2)
    await session.commit()
    
    conflicts = await service.check_event_conflicts(event1)
    assert len(conflicts) > 0
    assert event2.id in [c.id for c in conflicts]

@pytest.mark.asyncio
async def test_create_recurring_event(session: AsyncSession, sample_event_data):
    """Test creating a recurring event."""
    service = EventService(session)
    event, instances = await service.create_event(**sample_event_data)
    assert event.recurrence_pattern == RecurrencePattern.WEEKLY
    assert len(instances) > 0  # Should have recurring instances

@pytest.mark.asyncio
async def test_list_events_with_filters(session: AsyncSession, test_user):
    """Test listing events with filters."""
    service = EventService(session)
    all_events = await service.list_events(test_user.id)
    assert len(all_events) >= 3
    start_date = datetime.now()
    end_date = datetime.now() + timedelta(days=2)
    filtered_events = await service.list_events(
        test_user.id,
        start_date=start_date,
        end_date=end_date
    )
    assert len(filtered_events) == 2

@pytest.mark.asyncio
async def test_batch_create_events(session: AsyncSession, sample_event_data):
    """Test creating multiple events in a batch."""
    service = EventService(session)
    created_events = await service.batch_create_events([sample_event_data], sample_event_data["created_by"])
    assert len(created_events) == 1
    for event in created_events:
        assert event.created_by == sample_event_data["created_by"]

@pytest.mark.asyncio
async def test_event_permissions(session: AsyncSession, sample_event_data):
    """Test event permission checks."""
    service = EventService(session)
    creator_id = sample_event_data["created_by"]
    viewer_id = str(uuid.uuid4())
    
    # Create event
    event, _ = await service.create_event(**sample_event_data)
    
    # Test creator permissions
    assert await service._check_permission(event.id, creator_id, "view") is True
    assert await service._check_permission(event.id, creator_id, "edit_details") is True
    assert await service._check_permission(event.id, creator_id, "delete") is True
    
    # Test viewer permissions (should fail)
    assert await service._check_permission(event.id, viewer_id, "view") is False
    assert await service._check_permission(event.id, viewer_id, "edit_details") is False
    assert await service._check_permission(event.id, viewer_id, "delete") is False

@pytest.mark.asyncio
async def test_event_conflicts(session: AsyncSession, sample_event_data):
    """Test event conflict detection."""
    service = EventService(session)
    user_id = sample_event_data["created_by"]
    
    # Create first event
    event1, _ = await service.create_event(**sample_event_data)
    
    # Try to create conflicting event
    conflicting_data = sample_event_data.copy()
    conflicting_data["start_time"] = event1.start_time + timedelta(minutes=30)
    conflicting_data["end_time"] = event1.end_time - timedelta(minutes=30)
    
    # Should raise ValueError due to conflict
    with pytest.raises(ValueError):
        await service.create_event(**conflicting_data)

@pytest.mark.asyncio
async def test_get_event_version(session: AsyncSession, sample_event_data):
    """Test getting event version history."""
    service = EventService(session)
    version = await service.get_event_version(sample_event_data["id"], 1, sample_event_data["created_by"])
    assert version is not None
    assert version.event_id == sample_event_data["id"]
    assert version.version == 1 