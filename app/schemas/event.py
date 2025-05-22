from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID

if TYPE_CHECKING:
    from app.schemas.user import User

from app.models.event import RecurrencePattern, EventStatus
from app.core.models import SharePermission

class EventBase(BaseModel):
    """Base schema for event data."""
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    max_participants: Optional[int] = None
    status: EventStatus = EventStatus.DRAFT
    is_private: bool = False
    recurrence_pattern: RecurrencePattern = RecurrencePattern.NONE
    recurrence_end_date: Optional[datetime] = None
    recurrence_interval: Optional[int] = None
    recurrence_days: Optional[List[int]] = None
    recurrence_exceptions: Optional[List[str]] = None

class EventCreate(EventBase):
    """Schema for creating a new event."""
    created_by: str

class EventUpdate(BaseModel):
    """Schema for updating an existing event."""
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    max_participants: Optional[int] = None
    status: Optional[EventStatus] = None
    is_private: Optional[bool] = None
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_end_date: Optional[datetime] = None
    recurrence_interval: Optional[int] = None
    recurrence_days: Optional[List[int]] = None
    recurrence_exceptions: Optional[List[str]] = None

class EventInDB(EventBase):
    """Schema for event data as stored in the database."""
    id: str
    current_version: int
    created_by: str
    participant_count: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        orm_mode = True

class EventVersionInDB(BaseModel):
    id: UUID
    event_id: UUID
    version: int
    changes: dict
    created_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class BatchEventCreate(BaseModel):
    events: List[EventCreate]

class Event(EventBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    organizer_id: UUID
    organizer: "User"
    participants: List["User"] = []

    model_config = ConfigDict(from_attributes=True)

class EventShareCreate(BaseModel):
    user_id: UUID
    permission: SharePermission = SharePermission.VIEW
    expires_at: Optional[datetime] = None

class EventShare(BaseModel):
    id: UUID
    event_id: UUID
    user_id: UUID
    permission: SharePermission
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EventResponse(BaseModel):
    event: Event

class EventShareUsers(BaseModel):
    users: list
