from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Boolean, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship

from app.core.models import BaseModel

class NotificationType(str, Enum):
    """Types of notifications that can be sent."""
    EVENT_CREATED = "event_created"
    EVENT_UPDATED = "event_updated"
    EVENT_CANCELLED = "event_cancelled"
    EVENT_REMINDER = "event_reminder"
    SHARE_INVITATION = "share_invitation"
    ROLE_CHANGED = "role_changed"

class NotificationStatus(str, Enum):
    """Possible states of a notification."""
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"

class Notification(BaseModel):
    """Model for user notifications."""
    __tablename__ = "notifications"

    # Base fields are inherited from BaseModel:
    # id, created_at, updated_at, is_active

    # Foreign keys
    user_id = Column(String, ForeignKey("user.id"), nullable=False, index=True)
    
    # Notification specific fields
    message = Column(String, nullable=False)
    data = Column(JSON)  # Additional data for the notification
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.UNREAD, index=True)
    read_at = Column(DateTime, index=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")

    # Composite indexes
    __table_args__ = (
        Index('ix_notifications_user_status', 'user_id', 'status'),
        Index('ix_notifications_user_read_at', 'user_id', 'read_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "message": self.message,
            "data": self.data,
            "status": self.status.value,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class SharePermission(str, Enum):
    VIEW = "view"
    EDIT = "edit"
    MANAGE = "manage" 