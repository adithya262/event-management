from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.models import BaseModel

class SyncState(BaseModel):
    """Model for tracking client sync states."""
    __tablename__ = "sync_states"

    # Base fields: id, created_at, updated_at, is_active
    client_id = Column(String, nullable=False, index=True)
    user_id = Column(String, ForeignKey("user.id"), nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)
    last_sync_version = Column(Integer, nullable=False, default=0)
    last_sync_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    sync_token = Column(String, nullable=True, index=True)
    sync_metadata = Column(JSON, nullable=True)

    # Define relationship after User model is defined
    user = relationship("User", back_populates="sync_states", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "user_id": self.user_id,
            "entity_type": self.entity_type,
            "last_sync_version": self.last_sync_version,
            "last_sync_timestamp": self.last_sync_timestamp.isoformat(),
            "sync_token": self.sync_token,
            "metadata": self.sync_metadata,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        } 