from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.dependencies import get_current_user, check_permissions
from app.schemas.event import EventCreate, EventUpdate, EventResponse, EventShareUsers
from app.schemas.changelog import ChangelogResponse, DiffResponse, VersionHistoryEntry
from app.models.user import User, UserRole
from app.services.event import EventService
from app.services.changelog import ChangelogService
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=EventResponse)
async def create_event(
    *,
    db: AsyncSession = Depends(get_db),
    event_in: EventCreate,
    current_user: User = Depends(get_current_user)
) -> EventResponse:
    """Create a new event."""
    event_service = EventService(db)
    event, instances = await event_service.create_event(
        title=event_in.title,
        start_time=event_in.start_time,
        end_time=event_in.end_time,
        created_by=current_user.id,
        description=event_in.description,
        location=event_in.location,
        max_participants=event_in.max_participants,
        is_private=event_in.is_private,
        recurrence_pattern=event_in.recurrence_pattern,
        recurrence_end_date=event_in.recurrence_end_date,
        recurrence_interval=event_in.recurrence_interval,
        recurrence_days=event_in.recurrence_days,
        recurrence_exceptions=event_in.recurrence_exceptions
    )
    return EventResponse.from_orm(event)

@router.get("/", response_model=List[EventResponse])
async def list_events(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    include_created: bool = True,
    include_participating: bool = True
) -> List[EventResponse]:
    """List all events the user has access to with pagination and filtering."""
    event_service = EventService(db)
    events = await event_service.list_events(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Apply pagination
    total = len(events)
    events = events[skip:skip + limit]
    
    return [EventResponse.from_orm(event) for event in events]

@router.get("/{id}", response_model=EventResponse)
async def get_event(
    *,
    db: AsyncSession = Depends(get_db),
    id: str = Path(..., alias="id"),
    current_user: User = Depends(get_current_user)
) -> EventResponse:
    """Get a specific event by ID."""
    event_service = EventService(db)
    event = await event_service.get_event(id, current_user.id)
    return EventResponse.from_orm(event)

@router.put("/{id}", response_model=EventResponse)
async def update_event(
    *,
    db: AsyncSession = Depends(get_db),
    id: str = Path(..., alias="id"),
    event_in: EventUpdate,
    current_user: User = Depends(get_current_user)
) -> EventResponse:
    """Update an event by ID."""
    event_service = EventService(db)
    try:
        event = await event_service.update_event(
            event_id=id,
            updates=event_in.dict(exclude_unset=True),
            user_id=current_user.id
        )
        return EventResponse.from_orm(event)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    *,
    db: AsyncSession = Depends(get_db),
    id: str = Path(..., alias="id"),
    current_user: User = Depends(get_current_user)
):
    """Delete an event by ID."""
    event_service = EventService(db)
    try:
        await event_service.delete_event(event_id=id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("/batch", response_model=List[EventResponse])
async def create_events_batch(
    *,
    db: AsyncSession = Depends(get_db),
    events_in: List[EventCreate],
    current_user: User = Depends(get_current_user)
) -> List[EventResponse]:
    """Create multiple events in a single request."""
    event_service = EventService(db)
    
    created_events = await event_service.batch_create_events(
        [event.dict() for event in events_in],
        current_user.id
    )
    
    return [EventResponse.from_orm(event) for event in created_events]

@router.post("/{id}/share")
async def share_event(
    *,
    db: AsyncSession = Depends(get_db),
    id: str = Path(..., alias="id"),
    share_data: EventShareUsers,
    current_user: User = Depends(get_current_user)
):
    """Share an event with other users."""
    event_service = EventService(db)
    await event_service.share_event(event_id=id, share_data=share_data, user_id=current_user.id)
    return {"message": "Event shared successfully"}

@router.get("/{id}/permissions", response_model=List[Dict[str, Any]])
async def get_event_permissions(
    *,
    db: AsyncSession = Depends(get_db),
    id: str = Path(..., alias="id"),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List all permissions for an event."""
    event_service = EventService(db)
    try:
        permissions = await event_service.get_event_shares(event_id=id, user_id=current_user.id)
        return permissions
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.put("/{id}/permissions/{userId}", response_model=Dict[str, Any])
async def update_event_permissions(
    *,
    db: AsyncSession = Depends(get_db),
    id: str = Path(..., alias="id"),
    userId: str = Path(..., alias="userId"),
    permission_update: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update permissions for a user."""
    event_service = EventService(db)
    new_permission = permission_update.get("permission")
    if new_permission is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'permission' field is required in update data")

    try:
        updated_share = await event_service.update_event_share(
            event_id=id,
            target_user_id=userId,
            permission=new_permission,
            user_id=current_user.id
        )
        return updated_share
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.delete("/{id}/permissions/{userId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_permissions(
    *,
    db: AsyncSession = Depends(get_db),
    id: str = Path(..., alias="id"),
    userId: str = Path(..., alias="userId"),
    current_user: User = Depends(get_current_user)
):
    """Remove access for a user."""
    event_service = EventService(db)
    try:
        await event_service.delete_event_share(
            event_id=id,
            target_user_id=userId,
            user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("/{id}/rollback/{versionId}", response_model=EventResponse)
async def rollback_event_version(
    *,
    db: AsyncSession = Depends(get_db),
    id: str = Path(..., alias="id"),
    versionId: int = Path(..., alias="versionId"),
    current_user: User = Depends(get_current_user)
) -> EventResponse:
    """Rollback an event to a previous version."""
    event_service = EventService(db)
    try:
        event = await event_service.rollback_event(
            event_id=id,
            version_id=versionId,
            user_id=current_user.id
        )
        return EventResponse.from_orm(event)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/{id}/changelog", response_model=ChangelogResponse)
async def get_event_changelog(
    *,
    db: AsyncSession = Depends(get_db),
    id: str = Path(..., alias="id"),
    current_user: User = Depends(get_current_user)
) -> ChangelogResponse:
    """Get the changelog for an event."""
    event_service = EventService(db)
    try:
        changelog = await event_service.get_event_changelog(
            event_id=id,
            user_id=current_user.id
        )
        return changelog
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/{id}/diff/{versionId1}/{versionId2}", response_model=DiffResponse)
async def get_event_version_diff(
    *,
    db: AsyncSession = Depends(get_db),
    id: str = Path(..., alias="id"),
    versionId1: int = Path(..., alias="versionId1"),
    versionId2: int = Path(..., alias="versionId2"),
    current_user: User = Depends(get_current_user)
) -> DiffResponse:
    """Get the diff between two versions of an event."""
    event_service = EventService(db)
    try:
        diff = await event_service.get_event_version_diff(
            event_id=id,
            version_id1=versionId1,
            version_id2=versionId2,
            user_id=current_user.id
        )
        return diff
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) 