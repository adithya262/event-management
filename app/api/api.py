from fastapi import APIRouter

from app.api import auth, users, events

api_router = APIRouter()
 
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(events.router, prefix="/events", tags=["events"]) 