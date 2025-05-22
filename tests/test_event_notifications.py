import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio

@pytest.fixture
def test_event_data():
    """Test event data for creating test events."""
    return {
        "title": "Test Event",
        "description": "This is a test event",
        "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "end_time": (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat(),
        "location": "Test Location",
        "max_participants": 10,
        "is_private": False,
        "recurrence_pattern": None
    }

@pytest.mark.asyncio
async def test_event_data(session: AsyncSession):
    # ... existing test code ...
    pass

async def test_event_creation_notification(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test notification when an event is created."""
    # Register and login as organizer
    await client.post("/api/v1/users/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/users/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    token = login_response.json()["access_token"]
    
    # Create event
    response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {token}"},
        json=test_event_data
    )
    assert response.status_code == 200
    event_id = response.json()["id"]
    
    # Get notifications
    notifications_response = await client.get(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    
    # Verify event creation notification
    assert len(notifications) > 0
    event_notification = next(
        (n for n in notifications if n["type"] == "event_created" and n["event_id"] == event_id),
        None
    )
    assert event_notification is not None
    assert event_notification["title"] == "Event Created"
    assert test_event_data["title"] in event_notification["message"]

async def test_event_update_notification(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test notification when an event is updated."""
    # Register and login as organizer
    await client.post("/api/v1/users/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/users/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    token = login_response.json()["access_token"]
    
    # Create event
    create_response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {token}"},
        json=test_event_data
    )
    event_id = create_response.json()["id"]
    
    # Update event
    update_data = {
        "title": "Updated Event Title",
        "description": "Updated description"
    }
    await client.put(
        f"/api/v1/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=update_data
    )
    
    # Get notifications
    notifications_response = await client.get(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    
    # Verify event update notification
    event_notification = next(
        (n for n in notifications if n["type"] == "event_updated" and n["event_id"] == event_id),
        None
    )
    assert event_notification is not None
    assert event_notification["title"] == "Event Updated"
    assert update_data["title"] in event_notification["message"]

async def test_participant_join_notification(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test notification when a participant joins an event."""
    # Register and login as organizer
    await client.post("/api/v1/users/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/users/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    organizer_token = login_response.json()["access_token"]
    
    # Create event
    create_response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {organizer_token}"},
        json=test_event_data
    )
    event_id = create_response.json()["id"]
    
    # Register and login as participant
    participant_data = test_user_data.copy()
    participant_data.update({
        "email": "participant@example.com",
        "username": "participant"
    })
    await client.post("/api/v1/users/register", json=participant_data)
    participant_login = await client.post(
        "/api/v1/users/login",
        data={
            "username": participant_data["email"],
            "password": participant_data["password"]
        }
    )
    participant_token = participant_login.json()["access_token"]
    
    # Join event
    await client.post(
        f"/api/v1/events/{event_id}/join",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    
    # Get notifications for organizer
    organizer_notifications = await client.get(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert organizer_notifications.status_code == 200
    notifications = organizer_notifications.json()
    
    # Verify join notification for organizer
    join_notification = next(
        (n for n in notifications if n["type"] == "participant_joined" and n["event_id"] == event_id),
        None
    )
    assert join_notification is not None
    assert join_notification["title"] == "New Participant"
    assert participant_data["username"] in join_notification["message"]

async def test_event_reminder_notification(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test event reminder notification."""
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
    
    # Create event with reminder
    event_with_reminder = test_event_data.copy()
    event_with_reminder["reminder_time"] = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    
    response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {token}"},
        json=event_with_reminder
    )
    assert response.status_code == 200
    event_id = response.json()["id"]
    
    # Wait for reminder (in a real test, we would mock the time)
    # For now, we'll just verify the reminder was scheduled
    reminders_response = await client.get(
        f"/api/v1/events/{event_id}/reminders",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert reminders_response.status_code == 200
    reminders = reminders_response.json()
    assert len(reminders) > 0
    assert reminders[0]["event_id"] == event_id
    assert reminders[0]["reminder_time"] == event_with_reminder["reminder_time"]

async def test_event_cancellation_notification(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test notification when an event is cancelled."""
    # Register and login as organizer
    await client.post("/api/v1/users/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/users/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    token = login_response.json()["access_token"]
    
    # Create event
    create_response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {token}"},
        json=test_event_data
    )
    event_id = create_response.json()["id"]
    
    # Cancel event
    await client.post(
        f"/api/v1/events/{event_id}/cancel",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Get notifications
    notifications_response = await client.get(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    
    # Verify cancellation notification
    cancel_notification = next(
        (n for n in notifications if n["type"] == "event_cancelled" and n["event_id"] == event_id),
        None
    )
    assert cancel_notification is not None
    assert cancel_notification["title"] == "Event Cancelled"
    assert test_event_data["title"] in cancel_notification["message"]

async def test_participant_leave_notification(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test notification when a participant leaves an event."""
    # Register and login as organizer
    await client.post("/api/v1/users/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/users/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    organizer_token = login_response.json()["access_token"]
    
    # Create event
    create_response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {organizer_token}"},
        json=test_event_data
    )
    event_id = create_response.json()["id"]
    
    # Register and login as participant
    participant_data = test_user_data.copy()
    participant_data.update({
        "email": "participant@example.com",
        "username": "participant"
    })
    await client.post("/api/v1/users/register", json=participant_data)
    participant_login = await client.post(
        "/api/v1/users/login",
        data={
            "username": participant_data["email"],
            "password": participant_data["password"]
        }
    )
    participant_token = participant_login.json()["access_token"]
    
    # Join event
    await client.post(
        f"/api/v1/events/{event_id}/join",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    
    # Leave event
    await client.delete(
        f"/api/v1/events/{event_id}/leave",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    
    # Get notifications for organizer
    organizer_notifications = await client.get(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert organizer_notifications.status_code == 200
    notifications = organizer_notifications.json()
    
    # Verify leave notification for organizer
    leave_notification = next(
        (n for n in notifications if n["type"] == "participant_left" and n["event_id"] == event_id),
        None
    )
    assert leave_notification is not None
    assert leave_notification["title"] == "Participant Left"
    assert participant_data["username"] in leave_notification["message"]

async def test_event_full_notification(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test notification when an event reaches its participant limit."""
    # Register and login as organizer
    await client.post("/api/v1/users/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/users/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    organizer_token = login_response.json()["access_token"]
    
    # Create event with small participant limit
    event_data = test_event_data.copy()
    event_data["max_participants"] = 2
    create_response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {organizer_token}"},
        json=event_data
    )
    event_id = create_response.json()["id"]
    
    # Register and login as first participant
    participant1_data = test_user_data.copy()
    participant1_data.update({
        "email": "participant1@example.com",
        "username": "participant1"
    })
    await client.post("/api/v1/users/register", json=participant1_data)
    participant1_login = await client.post(
        "/api/v1/users/login",
        data={
            "username": participant1_data["email"],
            "password": participant1_data["password"]
        }
    )
    participant1_token = participant1_login.json()["access_token"]
    
    # Register and login as second participant
    participant2_data = test_user_data.copy()
    participant2_data.update({
        "email": "participant2@example.com",
        "username": "participant2"
    })
    await client.post("/api/v1/users/register", json=participant2_data)
    participant2_login = await client.post(
        "/api/v1/users/login",
        data={
            "username": participant2_data["email"],
            "password": participant2_data["password"]
        }
    )
    participant2_token = participant2_login.json()["access_token"]
    
    # First participant joins
    await client.post(
        f"/api/v1/events/{event_id}/join",
        headers={"Authorization": f"Bearer {participant1_token}"}
    )
    
    # Second participant joins
    await client.post(
        f"/api/v1/events/{event_id}/join",
        headers={"Authorization": f"Bearer {participant2_token}"}
    )
    
    # Get notifications for organizer
    organizer_notifications = await client.get(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert organizer_notifications.status_code == 200
    notifications = organizer_notifications.json()
    
    # Verify event full notification
    full_notification = next(
        (n for n in notifications if n["type"] == "event_full" and n["event_id"] == event_id),
        None
    )
    assert full_notification is not None
    assert full_notification["title"] == "Event Full"
    assert event_data["title"] in full_notification["message"]

async def test_recurring_event_notification(client: AsyncClient, test_user_data: dict):
    """Test notifications for recurring events."""
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
    
    # Create recurring event
    recurring_event_data = {
        "title": "Weekly Meeting",
        "description": "Weekly team meeting",
        "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "end_time": (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat(),
        "location": "Conference Room",
        "max_participants": 10,
        "is_private": False,
        "recurrence_pattern": {
            "frequency": "weekly",
            "interval": 1,
            "count": 4,
            "days_of_week": ["monday"],
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
    }
    
    response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {token}"},
        json=recurring_event_data
    )
    assert response.status_code == 200
    event_id = response.json()["id"]
    
    # Get notifications
    notifications_response = await client.get(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    
    # Verify recurring event creation notification
    event_notification = next(
        (n for n in notifications if n["type"] == "recurring_event_created" and n["event_id"] == event_id),
        None
    )
    assert event_notification is not None
    assert event_notification["title"] == "Recurring Event Created"
    assert recurring_event_data["title"] in event_notification["message"]
    assert "4 instances" in event_notification["message"]

async def test_notification_mark_as_read(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test marking notifications as read."""
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
    
    # Create event to generate notification
    response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {token}"},
        json=test_event_data
    )
    assert response.status_code == 200
    
    # Get notifications
    notifications_response = await client.get(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    assert len(notifications) > 0
    
    # Mark first notification as read
    notification_id = notifications[0]["id"]
    mark_read_response = await client.put(
        f"/api/v1/notifications/{notification_id}/read",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert mark_read_response.status_code == 200
    
    # Verify notification is marked as read
    updated_notifications = await client.get(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert updated_notifications.status_code == 200
    updated_notification = next(
        (n for n in updated_notifications.json() if n["id"] == notification_id),
        None
    )
    assert updated_notification is not None
    assert updated_notification["is_read"] is True 