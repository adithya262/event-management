import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio

@pytest.fixture
def test_recurring_event_data():
    """Test data for creating a recurring event."""
    return {
        "title": "Recurring Test Event",
        "description": "This is a recurring test event",
        "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "end_time": (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat(),
        "location": "Test Location",
        "max_participants": 10,
        "is_private": False,
        "recurrence_pattern": {
            "frequency": "weekly",
            "interval": 1,
            "count": 4,
            "days_of_week": ["monday", "wednesday", "friday"],
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
    }

async def test_create_recurring_event(client: AsyncClient, test_user_data: dict, test_recurring_event_data: dict):
    """Test creating a recurring event."""
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
    response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {token}"},
        json=test_recurring_event_data
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check event details
    assert data["title"] == test_recurring_event_data["title"]
    assert data["recurrence_pattern"] == test_recurring_event_data["recurrence_pattern"]
    
    # Get event instances
    instances_response = await client.get(
        f"/api/v1/events/{data['id']}/instances",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert instances_response.status_code == 200
    instances = instances_response.json()
    
    # Should have 4 instances (count=4)
    assert len(instances) == 4
    
    # Check that instances are on correct days
    for instance in instances:
        instance_date = datetime.fromisoformat(instance["start_time"])
        assert instance_date.weekday() in [0, 2, 4]  # Monday, Wednesday, Friday

async def test_update_recurring_event(client: AsyncClient, test_user_data: dict, test_recurring_event_data: dict):
    """Test updating a recurring event."""
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
    create_response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {token}"},
        json=test_recurring_event_data
    )
    event_id = create_response.json()["id"]
    
    # Update event
    update_data = {
        "title": "Updated Recurring Event",
        "recurrence_pattern": {
            "frequency": "weekly",
            "interval": 2,  # Changed from 1 to 2
            "count": 3,     # Changed from 4 to 3
            "days_of_week": ["tuesday", "thursday"],  # Changed days
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
    }
    response = await client.put(
        f"/api/v1/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check updated event details
    assert data["title"] == update_data["title"]
    assert data["recurrence_pattern"] == update_data["recurrence_pattern"]
    
    # Get updated event instances
    instances_response = await client.get(
        f"/api/v1/events/{event_id}/instances",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert instances_response.status_code == 200
    instances = instances_response.json()
    
    # Should have 3 instances (count=3)
    assert len(instances) == 3
    
    # Check that instances are on correct days
    for instance in instances:
        instance_date = datetime.fromisoformat(instance["start_time"])
        assert instance_date.weekday() in [1, 3]  # Tuesday, Thursday

async def test_cancel_recurring_event(client: AsyncClient, test_user_data: dict, test_recurring_event_data: dict):
    """Test canceling a recurring event."""
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
    create_response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {token}"},
        json=test_recurring_event_data
    )
    event_id = create_response.json()["id"]
    
    # Get event instances
    instances_response = await client.get(
        f"/api/v1/events/{event_id}/instances",
        headers={"Authorization": f"Bearer {token}"}
    )
    instances = instances_response.json()
    instance_id = instances[0]["id"]
    
    # Cancel specific instance
    cancel_response = await client.post(
        f"/api/v1/events/{event_id}/instances/{instance_id}/cancel",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert cancel_response.status_code == 200
    
    # Verify instance is canceled
    instance_response = await client.get(
        f"/api/v1/events/{event_id}/instances/{instance_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert instance_response.status_code == 200
    instance_data = instance_response.json()
    assert instance_data["status"] == "canceled"
    
    # Other instances should still be active
    instances_response = await client.get(
        f"/api/v1/events/{event_id}/instances",
        headers={"Authorization": f"Bearer {token}"}
    )
    instances = instances_response.json()
    for instance in instances:
        if instance["id"] != instance_id:
            assert instance["status"] == "active"

@pytest.mark.asyncio
async def test_recurring_event_data(session: AsyncSession):
    # ... existing test code ...
    pass 