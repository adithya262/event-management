from app.schemas.user import User, UserBase, UserCreate, UserUpdate, UserInDB
from app.schemas.event import Event, EventBase, EventCreate, EventUpdate

# Update forward references
User.model_rebuild()
Event.model_rebuild()
