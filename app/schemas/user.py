from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from app.core.models import UserRole

if TYPE_CHECKING:
    from app.schemas.event import Event

class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None

class UserRegister(UserBase):
    password: str
    is_active: bool = True
    is_superuser: bool = False
    role: UserRole = UserRole.VIEWER

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.VIEWER
    disabled: bool = False
    is_superuser: bool = False
    is_active: bool = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    disabled: Optional[bool] = None

class User(UserBase):
    id: UUID
    disabled: bool
    role: UserRole
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)

class UserInDB(UserBase):
    id: UUID
    role: UserRole
    is_superuser: bool
    disabled: bool

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class TokenPayload(BaseModel):
    sub: str  # subject (user id)
    exp: int  # expiration time
    jti: str  # JWT ID
