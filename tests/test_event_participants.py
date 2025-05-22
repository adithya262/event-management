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
        "max_participants": 2,  # Small number to test participant limits
        "is_private": False,
        "recurrence_pattern": None
    }

async def test_join_event(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test joining an event."""
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
    response = await client.post(
        f"/api/v1/events/{event_id}/join",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == event_id
    assert data["user_id"] is not None
    assert data["status"] == "confirmed"

async def test_leave_event(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test leaving an event."""
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
    response = await client.delete(
        f"/api/v1/events/{event_id}/leave",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 200
    
    # Verify participant is removed
    participants_response = await client.get(
        f"/api/v1/events/{event_id}/participants",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 200
    participants = participants_response.json()
    assert len(participants) == 0

async def test_event_participant_limit(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test event participant limit."""
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
    
    # Create event with max_participants = 2
    create_response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {organizer_token}"},
        json=test_event_data
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
    
    # Register and login as third participant
    participant3_data = test_user_data.copy()
    participant3_data.update({
        "email": "participant3@example.com",
        "username": "participant3"
    })
    await client.post("/api/v1/users/register", json=participant3_data)
    participant3_login = await client.post(
        "/api/v1/users/login",
        data={
            "username": participant3_data["email"],
            "password": participant3_data["password"]
        }
    )
    participant3_token = participant3_login.json()["access_token"]
    
    # First participant joins
    response1 = await client.post(
        f"/api/v1/events/{event_id}/join",
        headers={"Authorization": f"Bearer {participant1_token}"}
    )
    assert response1.status_code == 200
    
    # Second participant joins
    response2 = await client.post(
        f"/api/v1/events/{event_id}/join",
        headers={"Authorization": f"Bearer {participant2_token}"}
    )
    assert response2.status_code == 200
    
    # Third participant tries to join (should fail)
    response3 = await client.post(
        f"/api/v1/events/{event_id}/join",
        headers={"Authorization": f"Bearer {participant3_token}"}
    )
    assert response3.status_code == 400
    assert response3.json()["detail"] == "Event is full"

@pytest.mark.asyncio
async def test_event_data(session: AsyncSession):
    # ... existing test code ...
    pass 