import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event, EventStatus, RecurrencePattern
from app.models.user import User
from app.schemas.event import EventCreate, EventUpdate
from app.core.security.core_security import get_password_hash
from app.core.models import UserRole
from app.services.event import EventService

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def test_event_data():
    return {
        "title": "Test Event",
        "description": "Test Description",
        "start_time": datetime.utcnow(),
        "end_time": datetime.utcnow() + timedelta(hours=2),
        "location": "Test Location",
        "is_all_day": False,
        "is_recurring": False,
        "recurrence_rule": None,
        "status": "active"
    }

@pytest.fixture
async def test_user(session: AsyncSession):
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Test User",
        is_active=True,
        role=UserRole.USER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest.fixture
async def test_event(session: AsyncSession, test_user, test_event_data):
    """Create a test event."""
    event = Event(
        **test_event_data,
        creator_id=test_user.id
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event

@pytest.fixture
def event_data():
    return {
        "title": "Test Event",
        "description": "Test Description",
        "start_time": datetime.utcnow() + timedelta(days=1),
        "end_time": datetime.utcnow() + timedelta(days=1, hours=2),
        "location": "Test Location",
        "max_participants": 10,
        "status": EventStatus.DRAFT,
        "is_private": False,
        "recurrence_pattern": RecurrencePattern.NONE,
        "recurrence_end_date": None,
        "recurrence_interval": None,
        "recurrence_days": None,
        "recurrence_exceptions": None
    }

@pytest.mark.asyncio
async def test_create_event(db: AsyncSession, event_data, test_user):
    service = EventService(db)
    event_data["created_by"] = test_user.id
    event = await service.create_event(EventCreate(**event_data))
    
    assert event.title == event_data["title"]
    assert event.description == event_data["description"]
    assert event.start_time == event_data["start_time"]
    assert event.end_time == event_data["end_time"]
    assert event.location == event_data["location"]
    assert event.max_participants == event_data["max_participants"]
    assert event.status == event_data["status"]
    assert event.is_private == event_data["is_private"]
    assert event.created_by == test_user.id

@pytest.mark.asyncio
async def test_get_event(db: AsyncSession, event_data, test_user):
    service = EventService(db)
    event_data["created_by"] = test_user.id
    created_event = await service.create_event(EventCreate(**event_data))
    
    retrieved_event = await service.get_event(created_event.id)
    assert retrieved_event is not None
    assert retrieved_event.id == created_event.id
    assert retrieved_event.title == event_data["title"]

@pytest.mark.asyncio
async def test_update_event(db: AsyncSession, event_data, test_user):
    service = EventService(db)
    event_data["created_by"] = test_user.id
    created_event = await service.create_event(EventCreate(**event_data))
    
    update_data = EventUpdate(
        title="Updated Title",
        description="Updated Description"
    )
    
    updated_event = await service.update_event(created_event.id, update_data)
    assert updated_event is not None
    assert updated_event.title == "Updated Title"
    assert updated_event.description == "Updated Description"
    assert updated_event.start_time == event_data["start_time"]  # Unchanged fields should remain the same

@pytest.mark.asyncio
async def test_delete_event(db: AsyncSession, event_data, test_user):
    service = EventService(db)
    event_data["created_by"] = test_user.id
    created_event = await service.create_event(EventCreate(**event_data))
    
    success = await service.delete_event(created_event.id)
    assert success is True
    
    deleted_event = await service.get_event(created_event.id)
    assert deleted_event is None

@pytest.mark.asyncio
async def test_list_events(db: AsyncSession, event_data, test_user):
    service = EventService(db)
    event_data["created_by"] = test_user.id
    
    # Create multiple events
    events = []
    for i in range(3):
        event_data["title"] = f"Test Event {i}"
        event = await service.create_event(EventCreate(**event_data))
        events.append(event)
    
    # Test listing all events
    all_events = await service.list_events()
    assert len(all_events) >= 3
    
    # Test filtering by created_by
    user_events = await service.list_events(created_by=test_user.id)
    assert len(user_events) == 3
    
    # Test filtering by status
    draft_events = await service.list_events(status=EventStatus.DRAFT)
    assert len(draft_events) >= 3

@pytest.mark.asyncio
async def test_check_event_conflicts(db: AsyncSession, event_data, test_user):
    service = EventService(db)
    event_data["created_by"] = test_user.id
    
    # Create an initial event
    initial_event = await service.create_event(EventCreate(**event_data))
    
    # Test overlapping event
    overlapping_data = event_data.copy()
    overlapping_data["start_time"] = event_data["start_time"] + timedelta(minutes=30)
    overlapping_data["end_time"] = event_data["end_time"] + timedelta(minutes=30)
    
    conflicts = await service.check_event_conflicts(
        overlapping_data["start_time"],
        overlapping_data["end_time"],
        test_user.id
    )
    assert len(conflicts) == 1
    assert conflicts[0].id == initial_event.id
    
    # Test non-overlapping event
    non_overlapping_data = event_data.copy()
    non_overlapping_data["start_time"] = event_data["end_time"] + timedelta(hours=1)
    non_overlapping_data["end_time"] = event_data["end_time"] + timedelta(hours=3)
    
    conflicts = await service.check_event_conflicts(
        non_overlapping_data["start_time"],
        non_overlapping_data["end_time"],
        test_user.id
    )
    assert len(conflicts) == 0

@pytest.mark.asyncio
async def test_event_validation(session: AsyncSession, test_user):
    """Test event validation."""
    # Test end time before start time
    with pytest.raises(ValueError):
        EventCreate(
            title="Test Event",
            description="Test Description",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() - timedelta(hours=1),
            location="Test Location",
            creator_id=test_user.id
        )
    
    # Test missing required fields
    with pytest.raises(ValueError):
        EventCreate(
            title="Test Event",
            # Missing description
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=1),
            location="Test Location",
            creator_id=test_user.id
        )

@pytest.mark.asyncio
async def test_event_relationships(session: AsyncSession, test_event, test_user):
    """Test event relationships."""
    # Test event creator relationship
    assert test_event.creator.id == test_user.id
    assert test_event in test_user.events
    
    # Test event shares relationship
    assert test_event.shares == []
    
    # Test event participants relationship
    assert test_event.participants == []

@pytest.mark.asyncio
async def test_recurring_event(session: AsyncSession, test_user):
    """Test recurring event creation."""
    recurrence_rule = {
        "frequency": "weekly",
        "interval": 1,
        "count": 4,
        "days": ["monday", "wednesday", "friday"]
    }
    
    event_data = {
        "title": "Recurring Event",
        "description": "Test Recurring Event",
        "start_time": datetime.utcnow(),
        "end_time": datetime.utcnow() + timedelta(hours=1),
        "location": "Test Location",
        "is_all_day": False,
        "is_recurring": True,
        "recurrence_rule": recurrence_rule,
        "status": "active",
        "creator_id": test_user.id
    }
    
    event = Event(**event_data)
    session.add(event)
    await session.commit()
    await session.refresh(event)
    
    assert event.is_recurring
    assert event.recurrence_rule == recurrence_rule
    assert event.recurrence_rule["frequency"] == "weekly"
    assert event.recurrence_rule["count"] == 4

async def test_list_events(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test listing events."""
    # Register and login as user
    await client.post("/api/v1/users/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/users/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    token = login_response.json()["access_token"]
    
    # Create multiple events
    for i in range(3):
        event_data = test_event_data.copy()
        event_data["title"] = f"Test Event {i+1}"
        await client.post(
            "/api/v1/events/",
            headers={"Authorization": f"Bearer {token}"},
            json=event_data
        )
    
    # List events
    response = await client.get(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # At least 3 events should be returned

@pytest.mark.asyncio
async def test_event_data(session: AsyncSession):
    # ... existing test code ...
    pass 