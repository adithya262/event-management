from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.models import BaseModel

class EventVersion(BaseModel):
    """Model for tracking event versions and changes."""
    __tablename__ = "event_versions"
    __table_args__ = (
        UniqueConstraint('event_id', 'version', name='uix_event_version'),
        {'extend_existing': True}
    )

    # Base fields: id, created_at, updated_at, is_active
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    version = Column(Integer, nullable=False)
    created_by = Column(String, ForeignKey("user.id"), nullable=False)
    changes = Column(JSON, nullable=False)  # Stores the changes made in this version
    comment = Column(String, nullable=True)

    # Relationships
    event = relationship("Event", back_populates="versions")
    creator = relationship("User", back_populates="created_event_versions")

    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary representation."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "version": self.version,
            "created_by": self.created_by,
            "changes": self.changes,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def create_version(
        cls,
        event_id: str,
        created_by: str,
        changes: Dict[str, Any],
        comment: Optional[str] = None
    ) -> 'EventVersion':
        """Create a new version with the given changes."""
        return cls(
            event_id=event_id,
            created_by=created_by,
            changes=changes,
            comment=comment
        ) 