from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase
from enum import Enum

class Base(DeclarativeBase):
    pass

class SharePermission(str, Enum):
    VIEW = "view"
    EDIT = "edit"
    MANAGE = "manage"
    ADMIN = "admin"

class BaseModel(Base):
    __abstract__ = True
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"
    def __str__(self) -> str:
        return self.value
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.lower()
            for member in cls:
                if member.value == value:
                    return member
        return None 