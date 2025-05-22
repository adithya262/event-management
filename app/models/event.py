from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, TYPE_CHECKING, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer, Boolean, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, UserRole
from app.models.event_version import EventVersion

if TYPE_CHECKING:
    from app.models.user import User

class RecurrencePattern(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"

class EventStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Event(BaseModel):
    __tablename__ = "events"
    title = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    location = Column(String, nullable=True, index=True)
    max_participants = Column(Integer, nullable=True)
    status = Column(SQLEnum(
        EventStatus,
        name='eventstatus',
        create_constraint=True,
        validate_strings=True,
        native_enum=False,
        values_callable=lambda x: [e.value for e in x]
    ), default=EventStatus.DRAFT, index=True)
    is_private = Column(Boolean, default=False, index=True)
    recurrence_pattern = Column(SQLEnum(
        RecurrencePattern,
        name='recurrencepattern',
        create_constraint=True,
        validate_strings=True,
        native_enum=False,
        values_callable=lambda x: [e.value for e in x]
    ), default=RecurrencePattern.NONE)
    recurrence_end_date = Column(DateTime, nullable=True)
    recurrence_interval = Column(Integer, nullable=True)
    recurrence_days = Column(JSON, nullable=True)
    recurrence_exceptions = Column(JSON, nullable=True)
    current_version = Column(Integer, default=1)
    created_by = Column(String, ForeignKey("user.id"), nullable=False)
    creator = relationship("User", back_populates="created_events", foreign_keys=[created_by])
    participants = relationship(
        "User",
        secondary="event_participants",
        back_populates="events",
        viewonly=True
    )
    event_participations = relationship(
        "EventParticipant",
        back_populates="event",
        cascade="all, delete-orphan"
    )
    shares = relationship("EventShare", back_populates="event", cascade="all, delete-orphan")
    versions = relationship("EventVersion", back_populates="event", cascade="all, delete-orphan")
    __table_args__ = (
        Index('ix_events_date_range', 'start_time', 'end_time'),
        Index('ix_events_status_date', 'status', 'start_time'),
        Index('ix_events_creator_status', 'created_by', 'status'),
    )
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "location": self.location,
            "max_participants": self.max_participants,
            "status": self.status.value,
            "is_private": self.is_private,
            "recurrence_pattern": self.recurrence_pattern.value,
            "recurrence_end_date": self.recurrence_end_date.isoformat() if self.recurrence_end_date else None,
            "recurrence_interval": self.recurrence_interval,
            "recurrence_days": self.recurrence_days,
            "recurrence_exceptions": self.recurrence_exceptions,
            "current_version": self.current_version,
            "created_by": self.created_by,
            "participant_count": len(self.participants) if self.participants else 0,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active
        }
    def get_participant_role(self, user_id: str) -> Optional[str]:
        participation = next(
            (p for p in self.event_participations if p.user_id == user_id),
            None
        )
        return participation.role.value if participation else None
    def has_access(self, user_id: str, required_role: str = "viewer") -> bool:
        if self.created_by == user_id:
            return True
        role = self.get_participant_role(user_id)
        if not role:
            return False
        role_hierarchy = {
            "owner": 3,
            "editor": 2,
            "viewer": 1
        }
        return role_hierarchy[role] >= role_hierarchy[required_role]
    def check_conflict(self, other_event: 'Event') -> bool:
        if self.status == EventStatus.CANCELLED or other_event.status == EventStatus.CANCELLED:
            return False
        return (
            self.start_time < other_event.end_time and
            self.end_time > other_event.start_time
        )
    def get_recurring_instances(self) -> List['Event']:
        if self.recurrence_pattern == RecurrencePattern.NONE:
            return [self]
        instances = []
        current_start = self.start_time
        current_end = self.end_time
        duration = self.end_time - self.start_time
        while current_start <= self.recurrence_end_date:
            if current_start.strftime("%Y-%m-%d") not in self.recurrence_exceptions:
                instance = Event(
                    title=self.title,
                    start_time=current_start,
                    end_time=current_end,
                    created_by=self.created_by,
                    description=self.description,
                    location=self.location,
                    max_participants=self.max_participants,
                    is_private=self.is_private,
                    recurrence_pattern=RecurrencePattern.NONE
                )
                instances.append(instance)
            if self.recurrence_pattern == RecurrencePattern.DAILY:
                current_start += timedelta(days=self.recurrence_interval)
            elif self.recurrence_pattern == RecurrencePattern.WEEKLY:
                current_start += timedelta(weeks=self.recurrence_interval)
            elif self.recurrence_pattern == RecurrencePattern.MONTHLY:
                current_start += timedelta(days=30 * self.recurrence_interval)
            elif self.recurrence_pattern == RecurrencePattern.YEARLY:
                current_start += timedelta(days=365 * self.recurrence_interval)
            current_end = current_start + duration
        return instances
class EventParticipant(BaseModel):
    __tablename__ = "event_participants"
    event_id = Column(String, ForeignKey("events.id"), primary_key=True, index=True)
    user_id = Column(String, ForeignKey("user.id"), primary_key=True, index=True)
    role = Column(SQLEnum(UserRole, name="userrole", native_enum=True, values_callable=lambda x: [e.value for e in x]), default=UserRole.VIEWER, index=True)
    joined_at = Column(DateTime, default=datetime.utcnow, index=True)
    event = relationship("Event", back_populates="event_participations")
    user = relationship("User", back_populates="event_participations")
    __table_args__ = (
        Index('ix_event_participants_user_role', 'user_id', 'role'),
        Index('ix_event_participants_event_role', 'event_id', 'role'),
    )
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "role": self.role.value,
            "joined_at": self.joined_at.isoformat(),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
