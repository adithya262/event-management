import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta

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

async def test_event_version_history(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test event version history tracking."""
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
    
    # Create event
    create_response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {token}"},
        json=test_event_data
    )
    event_id = create_response.json()["id"]
    
    # Make first update
    update1 = {
        "title": "Updated Title 1",
        "description": "Updated description 1"
    }
    await client.put(
        f"/api/v1/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=update1
    )
    
    # Make second update
    update2 = {
        "title": "Updated Title 2",
        "location": "New Location"
    }
    await client.put(
        f"/api/v1/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=update2
    )
    
    # Get version history
    response = await client.get(
        f"/api/v1/events/{event_id}/versions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    versions = response.json()
    
    # Should have 3 versions: original + 2 updates
    assert len(versions) == 3
    
    # Check original version
    assert versions[0]["title"] == test_event_data["title"]
    assert versions[0]["description"] == test_event_data["description"]
    assert versions[0]["location"] == test_event_data["location"]
    
    # Check first update
    assert versions[1]["title"] == update1["title"]
    assert versions[1]["description"] == update1["description"]
    assert versions[1]["location"] == test_event_data["location"]
    
    # Check second update
    assert versions[2]["title"] == update2["title"]
    assert versions[2]["description"] == update1["description"]  # Should retain previous description
    assert versions[2]["location"] == update2["location"]

async def test_restore_event_version(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test restoring an event to a previous version."""
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
    
    # Create event
    create_response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {token}"},
        json=test_event_data
    )
    event_id = create_response.json()["id"]
    
    # Make an update
    update = {
        "title": "Updated Title",
        "description": "Updated description"
    }
    await client.put(
        f"/api/v1/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=update
    )
    
    # Get version history
    versions_response = await client.get(
        f"/api/v1/events/{event_id}/versions",
        headers={"Authorization": f"Bearer {token}"}
    )
    versions = versions_response.json()
    original_version_id = versions[0]["id"]
    
    # Restore to original version
    restore_response = await client.post(
        f"/api/v1/events/{event_id}/versions/{original_version_id}/restore",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert restore_response.status_code == 200
    restored_event = restore_response.json()
    
    # Verify restored event matches original version
    assert restored_event["title"] == test_event_data["title"]
    assert restored_event["description"] == test_event_data["description"]
    assert restored_event["location"] == test_event_data["location"]

async def test_version_metadata(client: AsyncClient, test_user_data: dict, test_event_data: dict):
    """Test version metadata (created_at, created_by, etc.)."""
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
    
    # Create event
    create_response = await client.post(
        "/api/v1/events/",
        headers={"Authorization": f"Bearer {token}"},
        json=test_event_data
    )
    event_id = create_response.json()["id"]
    
    # Make an update
    update = {
        "title": "Updated Title",
        "description": "Updated description"
    }
    await client.put(
        f"/api/v1/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=update
    )
    
    # Get version history
    response = await client.get(
        f"/api/v1/events/{event_id}/versions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    versions = response.json()
    
    # Check metadata for each version
    for version in versions:
        assert "id" in version
        assert "created_at" in version
        assert "created_by" in version
        assert "version_number" in version
        assert "changes" in version 