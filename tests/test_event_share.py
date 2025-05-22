import pytest
from datetime import datetime, timedelta
from app.models.event import Event
from app.models.event_share import EventShare, SharePermission
from app.models.user import User, UserRole
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def test_event(session: AsyncSession, test_user: User) -> Event:
    """Create a test event."""
    event = Event(
        title="Test Event",
        description="Test Description",
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=2),
        location="Test Location",
        created_by=test_user.id
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event

@pytest.mark.asyncio
async def test_create_share(session: AsyncSession, test_user: User, test_event: Event):
    """Test creating an event share."""
    share = EventShare(
        event_id=test_event.id,
        shared_by_id=test_user.id,
        shared_with_id=test_user.id,
        permission=SharePermission.VIEW
    )
    session.add(share)
    await session.commit()
    await session.refresh(share)
    
    assert share.event_id == test_event.id
    assert share.shared_by_id == test_user.id
    assert share.shared_with_id == test_user.id
    assert share.permission == SharePermission.VIEW

@pytest.mark.asyncio
async def test_share_permissions(session: AsyncSession, test_user: User, test_event: Event):
    """Test different share permission levels."""
    permissions = [SharePermission.VIEW, SharePermission.EDIT, SharePermission.MANAGE]
    
    for permission in permissions:
        share = EventShare(
            event_id=test_event.id,
            shared_by_id=test_user.id,
            shared_with_id=test_user.id,
            permission=permission
        )
        session.add(share)
        await session.commit()
        await session.refresh(share)
        
        assert share.permission == permission

@pytest.mark.asyncio
async def test_share_to_dict(session: AsyncSession, test_user: User, test_event: Event):
    """Test share serialization."""
    share = EventShare(
        event_id=test_event.id,
        shared_by_id=test_user.id,
        shared_with_id=test_user.id,
        permission=SharePermission.MANAGE
    )
    session.add(share)
    await session.commit()
    await session.refresh(share)
    
    share_dict = share.to_dict()
    assert share_dict["event_id"] == test_event.id
    assert share_dict["shared_by_id"] == test_user.id
    assert share_dict["shared_with_id"] == test_user.id
    assert share_dict["permission"] == SharePermission.MANAGE.value

@pytest.mark.asyncio
async def test_share_relationships(session: AsyncSession, test_user: User, test_event: Event):
    """Test share relationships."""
    share = EventShare(
        event_id=test_event.id,
        shared_by_id=test_user.id,
        shared_with_id=test_user.id,
        permission=SharePermission.VIEW
    )
    session.add(share)
    await session.commit()
    await session.refresh(share)
    
    # Test event relationship
    assert share.event.id == test_event.id
    assert share.event.title == test_event.title
    
    # Test user relationships
    assert share.shared_by.id == test_user.id
    assert share.shared_with.id == test_user.id

@pytest.mark.asyncio
async def test_share_permission_levels(session: AsyncSession, test_user: User, test_event: Event):
    """Test share permission level comparisons."""
    view_share = EventShare(
        event_id=test_event.id,
        shared_by_id=test_user.id,
        shared_with_id=test_user.id,
        permission=SharePermission.VIEW
    )
    
    edit_share = EventShare(
        event_id=test_event.id,
        shared_by_id=test_user.id,
        shared_with_id=test_user.id,
        permission=SharePermission.EDIT
    )
    
    manage_share = EventShare(
        event_id=test_event.id,
        shared_by_id=test_user.id,
        shared_with_id=test_user.id,
        permission=SharePermission.MANAGE
    )
    
    assert view_share.permission.value < edit_share.permission.value
    assert edit_share.permission.value < manage_share.permission.value
    assert view_share.permission.value < manage_share.permission.value 