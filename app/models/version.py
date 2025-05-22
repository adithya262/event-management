from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.core.models import BaseModel
from uuid import uuid4

class Version(BaseModel):
    """Model for versioning."""
    __tablename__ = "versions"

    # Base fields are inherited from BaseModel:
    # id, created_at, updated_at, is_active

    # Foreign keys
    created_by = Column(String, ForeignKey("user.id"), nullable=False)
    
    # Version specific fields
    entity_type = Column(String, nullable=False)  # e.g., "event", "user"
    entity_id = Column(String, nullable=False)
    version_number = Column(Integer, nullable=False)
    changes = Column(JSON)
    previous_state = Column(JSON)
    current_state = Column(JSON)
    
    # Relationships
    creator = relationship("User", back_populates="created_versions")

    def get_diff(self) -> Dict[str, Any]:
        """Calculate differences between previous and current states."""
        if not self.previous_state or not self.current_state:
            return {}
        
        diff = {}
        for key in set(self.previous_state.keys()) | set(self.current_state.keys()):
            if key not in self.previous_state:
                diff[key] = {"added": self.current_state[key]}
            elif key not in self.current_state:
                diff[key] = {"removed": self.previous_state[key]}
            elif self.previous_state[key] != self.current_state[key]:
                diff[key] = {
                    "from": self.previous_state[key],
                    "to": self.current_state[key]
                }
        return diff

    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary representation."""
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "version_number": self.version_number,
            "changes": self.changes,
            "previous_state": self.previous_state,
            "current_state": self.current_state,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        } 