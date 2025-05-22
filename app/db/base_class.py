from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.core.models import Base, BaseModel

# Only export Base and BaseModel from here
__all__ = [
    "BaseModel",
    "Base"
] 