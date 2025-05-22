from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Changelog(Base):
    """Model for tracking application changes and versions."""
    
    __tablename__ = "changelog"
    
    id = Column(String, primary_key=True, index=True)
    version = Column(String, nullable=False, index=True)
    changes = Column(JSON, nullable=False)
    release_date = Column(DateTime, nullable=False)
    created_by = Column(String, ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="changelogs")
    
    def __repr__(self):
        return f"<Changelog {self.version}>"

# Attach the relationship to User after both classes are defined
from app.models.user import User
User.changelogs = relationship("Changelog", back_populates="creator") 