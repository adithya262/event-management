from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, desc
from sqlalchemy.sql import select
from datetime import datetime

from app.api.v1.dependencies import get_current_active_user, get_db
from app.core.security.roles import owner_required, editor_required, viewer_required
from app.models.user import User
from app.schemas.event import Event as EventSchema, EventCreate, EventUpdate, EventShareCreate
from app.services.event_service import (
    create_event,
    get_event,
    get_events,
    update_event,
    delete_event,
    add_participant,
    remove_participant,
    share_event
)
from app.models.event_share import EventShare
from app.models.version import Version

router = APIRouter()

@router.get("/", response_model=List[EventSchema])
async def read_events(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(viewer_required),
):
    events = await get_events(db, skip=skip, limit=limit)
    return events

@router.post("/", response_model=EventSchema)
async def create_new_event(
    event: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(editor_required),
):
    return await create_event(db=db, event=event, organizer_id=current_user.id)

@router.get("/{event_id}", response_model=EventSchema)
async def read_event(
    event_id: int,
    current_user: User = Depends(viewer_required),
    db: AsyncSession = Depends(get_db),
):
    event = await get_event(db, event_id=event_id)
    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )
    return event

@router.put("/{event_id}", response_model=EventSchema)
async def update_event_by_id(
    event_id: int,
    event_in: EventUpdate,
    current_user: User = Depends(editor_required),
    db: AsyncSession = Depends(get_db),
):
    event = await get_event(db, event_id=event_id)
    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )
    if event.organizer_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=400,
            detail="Not enough permissions"
        )
    try:
        event = await update_event(db=db, event_id=event_id, event=event_in)
    except Exception as e:
        if "Conflict" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise
    return event

@router.delete("/{event_id}", response_model=EventSchema)
async def delete_event_by_id(
    event_id: int,
    current_user: User = Depends(owner_required),
    db: AsyncSession = Depends(get_db),
):
    event = await get_event(db, event_id=event_id)
    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )
    if event.organizer_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=400,
            detail="Not enough permissions"
        )
    event = await delete_event(db=db, event_id=event_id)
    return event

@router.post("/{event_id}/participants/{user_id}", response_model=EventSchema)
async def add_event_participant(
    event_id: int,
    user_id: int,
    current_user: User = Depends(editor_required),
    db: AsyncSession = Depends(get_db),
):
    event = await get_event(db, event_id=event_id)
    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )
    if event.organizer_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=400,
            detail="Not enough permissions"
        )
    event = await add_participant(db=db, event_id=event_id, user_id=user_id)
    return event

@router.delete("/{event_id}/participants/{user_id}", response_model=EventSchema)
async def remove_event_participant(
    event_id: int,
    user_id: int,
    current_user: User = Depends(editor_required),
    db: AsyncSession = Depends(get_db),
):
    event = await get_event(db, event_id=event_id)
    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )
    if event.organizer_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=400,
            detail="Not enough permissions"
        )
    event = await remove_participant(db=db, event_id=event_id, user_id=user_id)
    return event

@router.post("/{event_id}/share")
async def share_event_endpoint(
    event_id: str,
    share_data: EventShareCreate,
    current_user: User = Depends(editor_required),
    db: AsyncSession = Depends(get_db),
):
    try:
        new_share = await share_event(db, event_id, current_user, share_data)
        return new_share.to_dict()
    except Exception as e:
        msg = str(e)
        if "permission" in msg.lower():
            raise HTTPException(status_code=403, detail=msg)
        elif "already has access" in msg.lower():
            raise HTTPException(status_code=400, detail=msg)
        elif "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        else:
            raise HTTPException(status_code=400, detail=msg)

@router.get("/{event_id}/at", response_model=EventSchema)
async def get_event_at_time(
    event_id: int,
    timestamp: datetime = Query(..., description="Timestamp to query event state at"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(viewer_required),
):
    # Find the latest version as of the timestamp
    result = await db.execute(
        select(Version)
        .where(
            Version.entity_type == "event",
            Version.entity_id == str(event_id),
            Version.created_at <= timestamp
        )
        .order_by(desc(Version.version_number))
        .limit(1)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="No event version found at that time")
    # Return the event state as of that version
    return version.current_state
