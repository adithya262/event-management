from datetime import datetime
from typing import Optional, List, TYPE_CHECKING, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.models import BaseModel, UserRole
import uuid

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.sync_state import SyncState

class User(BaseModel):
    __tablename__ = "user"
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(SQLEnum(UserRole, name="userrole", native_enum=True, values_callable=lambda x: [e.value for e in x]), nullable=False, default=UserRole.USER)
    is_superuser = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_events = relationship("Event", back_populates="creator", foreign_keys="[Event.created_by]")
    shared_events = relationship(
        "EventShare",
        foreign_keys="[EventShare.shared_by_id]",
        back_populates="shared_by"
    )
    received_shares = relationship(
        "EventShare",
        foreign_keys="[EventShare.shared_with_id]",
        back_populates="shared_with"
    )
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    created_versions = relationship("Version", back_populates="creator", cascade="all, delete-orphan")
    created_event_versions = relationship("EventVersion", back_populates="creator", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    sync_states = relationship("SyncState", back_populates="user", lazy="joined", cascade="all, delete-orphan")
    events = relationship(
        "Event",
        secondary="event_participants",
        back_populates="participants",
        viewonly=True
    )
    event_participations = relationship(
        "EventParticipant",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    @property
    def event_shares(self):
        return self.shared_events + self.received_shares
    @property
    def disabled(self) -> bool:
        return not self.is_active
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = datetime.utcnow()
        if not self.username and self.email:
            self.username = self.email.split('@')[0]
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role.value if self.role else None,
            "is_superuser": self.is_superuser,
            "is_active": self.is_active,
            "disabled": not self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    def __repr__(self):
        return f"<User {self.email}>"
