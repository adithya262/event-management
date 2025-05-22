from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.models import Base, SharePermission
from uuid import uuid4
from app.models.user import UserRole
from enum import Enum

class SharePermission(Enum):
    """Share permission enum."""
    VIEW = "view"
    EDIT = "edit"
    MANAGE = "manage"

class EventShare(Base):
    """Model for event sharing."""
    __tablename__ = "event_share"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    shared_by_id = Column(String, ForeignKey("user.id"), nullable=False)
    shared_with_id = Column(String, ForeignKey("user.id"), nullable=False)
    permission = Column(SQLEnum(SharePermission), nullable=False, default=SharePermission.VIEW)
    expires_at = Column(DateTime)
    
    # Relationships
    event = relationship("Event", back_populates="shares")
    shared_by = relationship("User", foreign_keys=[shared_by_id], back_populates="shared_events")
    shared_with = relationship("User", foreign_keys=[shared_with_id], back_populates="received_shares")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.id:
            self.id = str(uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = datetime.utcnow()
        self.expires_at = kwargs.get('expires_at')

    def to_dict(self) -> Dict[str, Any]:
        """Convert share to dictionary representation."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "shared_by_id": self.shared_by_id,
            "shared_with_id": self.shared_with_id,
            "permission": self.permission.value if self.permission else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def has_permission(self, required_permission: SharePermission) -> bool:
        """Check if the share has the required permission level."""
        permission_levels = {
            SharePermission.VIEW: 1,
            SharePermission.EDIT: 2,
            SharePermission.MANAGE: 3
        }
        return permission_levels[self.permission] >= permission_levels[required_permission]
    
    def can_perform_action(self, action: str) -> bool:
        """Check if the share allows a specific action."""
        action_permissions = {
            "view": True,  # Everyone with a share can view
            "edit": self.permission in [SharePermission.EDIT, SharePermission.MANAGE],
            "delete": self.permission in [SharePermission.MANAGE],
            "share": self.permission in [SharePermission.MANAGE]
        }
        return action_permissions.get(action, False) 