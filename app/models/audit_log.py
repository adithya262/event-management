from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.models import BaseModel
from enum import Enum

class AuditAction(str, Enum):
    """Enum for audit log actions."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SHARE = "share"
    UNSHARE = "unshare"
    JOIN = "join"
    LEAVE = "leave"
    STATUS_CHANGE = "status_change"

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}

    # Base fields: id, created_at, updated_at, is_active
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    details = Column(JSON, nullable=True)

    user = relationship("User", back_populates="audit_logs")

    def to_dict(self):
        """Convert audit log to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        } 