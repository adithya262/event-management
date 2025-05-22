import pytest
from datetime import datetime, timedelta
from app.services.changelog import ChangelogService
from app.models.version import Version
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from sqlalchemy import delete
from app.models.changelog import Changelog
from app.core.security.core_security import get_password_hash
from app.core.models import UserRole

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
async def test_changelog(session: AsyncSession, test_user):
    """Create a test changelog entry."""
    changelog = Changelog(
        version="1.0.0",
        changes=["Initial release"],
        release_date=datetime.utcnow(),
        created_by=test_user.id
    )
    session.add(changelog)
    await session.commit()
    await session.refresh(changelog)
    return changelog

@pytest.fixture
async def clean_versions(session: AsyncSession):
    """Clean up all versions before each test."""
    await session.execute(delete(Version))
    await session.commit()

@pytest.fixture
def sample_versions(test_user):
    """Create sample versions for testing."""
    entity_id = str(uuid4())  # Unique entity ID for each test
    return {
        "entity_id": entity_id,
        "versions": [
            {
                "entity_type": "event",
                "entity_id": entity_id,
                "version_number": 1,
                "current_state": {
                    "title": "Initial Event",
                    "description": "First version",
                    "location": "Room A"
                },
                "created_at": datetime.now() - timedelta(days=2),
                "created_by": test_user.id
            },
            {
                "entity_type": "event",
                "entity_id": entity_id,
                "version_number": 2,
                "current_state": {
                    "title": "Updated Event",
                    "description": "Second version",
                    "location": "Room B",
                    "max_participants": 10
                },
                "created_at": datetime.now() - timedelta(days=1),
                "created_by": test_user.id
            },
            {
                "entity_type": "event",
                "entity_id": entity_id,
                "version_number": 3,
                "current_state": {
                    "title": "Final Event",
                    "description": "Third version",
                    "location": "Room C",
                    "max_participants": 20,
                    "status": "active"
                },
                "created_at": datetime.now(),
                "created_by": test_user.id
            }
        ]
    }

@pytest.mark.asyncio
async def test_get_entity_changelog(session: AsyncSession, sample_versions, test_user, clean_versions):
    """Test retrieving complete changelog for an entity."""
    # Create versions in database
    for version_data in sample_versions["versions"]:
        version = Version(**version_data)
        session.add(version)
    await session.commit()
    
    # Initialize service and get changelog
    service = ChangelogService(session)
    changelog = await service.get_entity_changelog("event", sample_versions["entity_id"])
    
    # Verify results
    assert len(changelog) == 3
    assert changelog[0]["version_number"] == 1
    assert changelog[1]["version_number"] == 2
    assert changelog[2]["version_number"] == 3
    assert all(v["created_by"] == test_user.id for v in changelog)

@pytest.mark.asyncio
async def test_get_changes_between_versions(session: AsyncSession, sample_versions, test_user, clean_versions):
    """Test retrieving changes between specific versions."""
    # Create versions in database
    for version_data in sample_versions["versions"]:
        version = Version(**version_data)
        session.add(version)
    await session.commit()
    
    # Initialize service
    service = ChangelogService(session)
    
    # Get changes between versions 1 and 2
    changes = await service.get_changes_between_versions(
        "event",
        sample_versions["entity_id"],
        1,
        2
    )
    
    # Verify changes
    assert changes["title"] == "Updated Event"
    assert changes["location"] == "Room B"
    assert "max_participants" in changes
    assert changes["max_participants"] == 10

@pytest.mark.asyncio
async def test_generate_unified_diff(session: AsyncSession, sample_versions, test_user, clean_versions):
    """Test generating unified diff between versions."""
    # Create versions in database
    for version_data in sample_versions["versions"]:
        version = Version(**version_data)
        session.add(version)
    await session.commit()
    
    # Initialize service
    service = ChangelogService(session)
    
    # Generate diff between versions 1 and 3
    diff = await service.generate_unified_diff(
        "event",
        sample_versions["entity_id"],
        1,
        3
    )
    
    # Verify diff contains expected changes
    assert "title" in diff
    assert "location" in diff
    assert "max_participants" in diff
    assert "status" in diff

@pytest.mark.asyncio
async def test_date_filtered_changelog(session: AsyncSession, sample_versions, test_user, clean_versions):
    """Test retrieving changelog filtered by date range."""
    # Create versions in database
    for version_data in sample_versions["versions"]:
        version = Version(**version_data)
        session.add(version)
    await session.commit()
    
    # Initialize service
    service = ChangelogService(session)
    
    # Get changelog for last 2 days
    start_date = datetime.now() - timedelta(days=2)
    end_date = datetime.now()
    
    changelog = await service.get_entity_changelog(
        "event",
        sample_versions["entity_id"],
        start_date=start_date,
        end_date=end_date
    )
    
    # Verify results
    assert len(changelog) == 3
    assert all(start_date <= v["created_at"] <= end_date for v in changelog)

@pytest.mark.asyncio
async def test_invalid_version_comparison(session: AsyncSession, sample_versions, test_user, clean_versions):
    """Test error handling for invalid version comparisons."""
    # Create versions in database
    for version_data in sample_versions["versions"]:
        version = Version(**version_data)
        session.add(version)
    await session.commit()
    
    # Initialize service
    service = ChangelogService(session)
    
    # Test with non-existent version
    with pytest.raises(ValueError):
        await service.get_changes_between_versions("event", sample_versions["entity_id"], 1, 999)
    
    # Test with invalid version order
    with pytest.raises(ValueError):
        await service.get_changes_between_versions("event", sample_versions["entity_id"], 3, 1)

@pytest.mark.asyncio
async def test_create_changelog(session: AsyncSession, test_user):
    """Test changelog creation."""
    changelog = Changelog(
        version="1.0.0",
        changes=["Initial release", "Added basic features"],
        release_date=datetime.utcnow(),
        created_by=test_user.id
    )
    session.add(changelog)
    await session.commit()
    await session.refresh(changelog)
    
    assert changelog.version == "1.0.0"
    assert len(changelog.changes) == 2
    assert changelog.release_date is not None
    assert changelog.created_by == test_user.id
    assert changelog.created_at is not None
    assert changelog.updated_at is not None

@pytest.mark.asyncio
async def test_get_changelog(session: AsyncSession, test_changelog):
    """Test getting a changelog entry."""
    changelog = await session.get(Changelog, test_changelog.id)
    assert changelog is not None
    assert changelog.version == test_changelog.version
    assert changelog.changes == test_changelog.changes
    assert changelog.created_by == test_changelog.created_by

@pytest.mark.asyncio
async def test_update_changelog(session: AsyncSession, test_changelog):
    """Test updating a changelog entry."""
    new_changes = ["Updated feature", "Bug fixes"]
    test_changelog.changes = new_changes
    
    await session.commit()
    await session.refresh(test_changelog)
    
    assert test_changelog.changes == new_changes
    assert test_changelog.updated_at > test_changelog.created_at

@pytest.mark.asyncio
async def test_delete_changelog(session: AsyncSession, test_changelog):
    """Test deleting a changelog entry."""
    await session.delete(test_changelog)
    await session.commit()
    
    deleted_changelog = await session.get(Changelog, test_changelog.id)
    assert deleted_changelog is None

@pytest.mark.asyncio
async def test_changelog_validation(session: AsyncSession, test_user):
    """Test changelog validation."""
    # Test invalid version format
    with pytest.raises(ValueError):
        Changelog(
            version="invalid-version",
            changes=["Test change"],
            release_date=datetime.utcnow(),
            created_by=test_user.id
        )
    
    # Test empty changes list
    with pytest.raises(ValueError):
        Changelog(
            version="1.0.0",
            changes=[],
            release_date=datetime.utcnow(),
            created_by=test_user.id
        )
    
    # Test missing required fields
    with pytest.raises(ValueError):
        Changelog(
            version="1.0.0",
            # Missing changes
            release_date=datetime.utcnow(),
            created_by=test_user.id
        )

@pytest.mark.asyncio
async def test_changelog_relationships(session: AsyncSession, test_changelog, test_user):
    """Test changelog relationships."""
    # Test creator relationship
    assert test_changelog.creator.id == test_user.id
    assert test_changelog in test_user.changelogs

@pytest.mark.asyncio
async def test_changelog_versioning(session: AsyncSession, test_user):
    """Test changelog versioning."""
    # Create multiple versions
    versions = [
        ("1.0.0", ["Initial release"]),
        ("1.0.1", ["Bug fixes"]),
        ("1.1.0", ["New features"]),
        ("2.0.0", ["Major update"])
    ]
    
    for version, changes in versions:
        changelog = Changelog(
            version=version,
            changes=changes,
            release_date=datetime.utcnow(),
            created_by=test_user.id
        )
        session.add(changelog)
    
    await session.commit()
    
    # Verify versions are stored correctly
    for version, changes in versions:
        changelog = await session.query(Changelog).filter(Changelog.version == version).first()
        assert changelog is not None
        assert changelog.changes == changes 