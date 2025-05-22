import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio

@pytest.fixture
def test_events_data():
    """Test data for creating multiple events with different attributes."""
    base_time = datetime.utcnow() + timedelta(days=1)
    return [
        {
            "title": "Public Event 1",
            "description": "First public event",
            "start_time": base_time.isoformat(),
            "end_time": (base_time + timedelta(hours=2)).isoformat(),
            "location": "Location A",
            "max_participants": 10,
            "is_private": False,
            "recurrence_pattern": None
        },
        {
            "title": "Private Event",
            "description": "A private event",
            "start_time": (base_time + timedelta(days=1)).isoformat(),
            "end_time": (base_time + timedelta(days=1, hours=2)).isoformat(),
            "location": "Location B",
            "max_participants": 5,
            "is_private": True,
            "recurrence_pattern": None
        },
        {
            "title": "Public Event 2",
            "description": "Second public event",
            "start_time": (base_time + timedelta(days=2)).isoformat(),
            "end_time": (base_time + timedelta(days=2, hours=2)).isoformat(),
            "location": "Location A",
            "max_participants": 15,
            "is_private": False,
            "recurrence_pattern": None
        }
    ]

@pytest.mark.asyncio
async def test_events_data(session: AsyncSession):
    # ... existing test code ...
    pass

async def test_search_events_by_title(client: AsyncClient, test_user_data: dict, test_events_data: list):
    """Test searching events by title."""
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
    
    # Create test events
    for event_data in test_events_data:
        await client.post(
            "/api/v1/events/",
            headers={"Authorization": f"Bearer {token}"},
            json=event_data
        )
    
    # Search for events with "Public" in title
    response = await client.get(
        "/api/v1/events/search?title=Public",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 2
    for event in events:
        assert "Public" in event["title"]

async def test_filter_events_by_location(client: AsyncClient, test_user_data: dict, test_events_data: list):
    """Test filtering events by location."""
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
    
    # Create test events
    for event_data in test_events_data:
        await client.post(
            "/api/v1/events/",
            headers={"Authorization": f"Bearer {token}"},
            json=event_data
        )
    
    # Filter events by location
    response = await client.get(
        "/api/v1/events/search?location=Location A",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 2
    for event in events:
        assert event["location"] == "Location A"

async def test_filter_events_by_date_range(client: AsyncClient, test_user_data: dict, test_events_data: list):
    """Test filtering events by date range."""
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
    
    # Create test events
    for event_data in test_events_data:
        await client.post(
            "/api/v1/events/",
            headers={"Authorization": f"Bearer {token}"},
            json=event_data
        )
    
    # Calculate date range
    start_date = datetime.utcnow() + timedelta(days=1)
    end_date = start_date + timedelta(days=1)
    
    # Filter events by date range
    response = await client.get(
        f"/api/v1/events/search?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 2  # Should include events on day 1 and 2
    
    for event in events:
        event_start = datetime.fromisoformat(event["start_time"])
        assert start_date <= event_start <= end_date

async def test_filter_public_events(client: AsyncClient, test_user_data: dict, test_events_data: list):
    """Test filtering public events."""
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
    
    # Create test events
    for event_data in test_events_data:
        await client.post(
            "/api/v1/events/",
            headers={"Authorization": f"Bearer {token}"},
            json=event_data
        )
    
    # Filter public events
    response = await client.get(
        "/api/v1/events/search?is_private=false",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 2
    for event in events:
        assert not event["is_private"]

async def test_combined_search_filters(client: AsyncClient, test_user_data: dict, test_events_data: list):
    """Test combining multiple search filters."""
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
    
    # Create test events
    for event_data in test_events_data:
        await client.post(
            "/api/v1/events/",
            headers={"Authorization": f"Bearer {token}"},
            json=event_data
        )
    
    # Search with multiple filters
    response = await client.get(
        "/api/v1/events/search?title=Public&location=Location A&is_private=false",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 2
    
    for event in events:
        assert "Public" in event["title"]
        assert event["location"] == "Location A"
        assert not event["is_private"] 