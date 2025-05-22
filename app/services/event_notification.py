from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from app.models.event import Event, EventStatus
from app.models.event_share import EventShare
from app.models.user import User
import logging
import json
from app.core.notification import NotificationService

logger = logging.getLogger(__name__)

class EventNotificationService:
    """Service for handling event-related notifications."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_service = NotificationService()
    
    async def notify_event_created(self, event: Event) -> None:
        """Send notifications when an event is created."""
        # Notify creator
        await self.notification_service.create_notification(
            user_id=event.created_by,
            title="Event Created",
            message=f"Your event '{event.title}' has been created successfully.",
            notification_type="event_created",
            data=event.to_dict()
        )
        
        # If event is public, notify all users
        if not event.is_private:
            stmt = select(User)
            result = await self.session.execute(stmt)
            users = result.scalars().all()
            for user in users:
                if user.id != event.created_by:
                    await self.notification_service.create_notification(
                        user_id=user.id,
                        title="New Public Event",
                        message=f"A new public event '{event.title}' has been created.",
                        notification_type="public_event_created",
                        data=event.to_dict()
                    )
    
    async def notify_event_updated(
        self,
        event: Event,
        updates: Dict[str, Any],
        updated_by: str
    ) -> None:
        """Send notifications when an event is updated."""
        # Get all users who should be notified
        users_to_notify = await self._get_users_to_notify(event)
        
        # Create notification for each user
        for user_id in users_to_notify:
            if user_id != updated_by:  # Don't notify the user who made the changes
                await self.notification_service.create_notification(
                    user_id=user_id,
                    title="Event Updated",
                    message=f"The event '{event.title}' has been updated.",
                    notification_type="event_updated",
                    data={
                        "event": event.to_dict(),
                        "updates": updates,
                        "updated_by": updated_by
                    }
                )
    
    async def notify_event_deleted(self, event: Event, deleted_by: str) -> None:
        """Send notifications when an event is deleted."""
        # Get all users who should be notified
        users_to_notify = await self._get_users_to_notify(event)
        
        # Create notification for each user
        for user_id in users_to_notify:
            if user_id != deleted_by:  # Don't notify the user who deleted the event
                await self.notification_service.create_notification(
                    user_id=user_id,
                    title="Event Deleted",
                    message=f"The event '{event.title}' has been deleted.",
                    notification_type="event_deleted",
                    data=event.to_dict()
                )
    
    async def notify_event_reminder(self, event: Event) -> None:
        """Send reminder notifications for an upcoming event."""
        # Get all users who should be notified
        users_to_notify = await self._get_users_to_notify(event)
        
        # Create reminder notification for each user
        for user_id in users_to_notify:
            await self.notification_service.create_notification(
                user_id=user_id,
                title="Event Reminder",
                message=f"Reminder: The event '{event.title}' is starting soon.",
                notification_type="event_reminder",
                data=event.to_dict()
            )
    
    async def notify_participant_joined(
        self,
        event: Event,
        participant_id: str
    ) -> None:
        """Send notifications when a participant joins an event."""
        # Notify event creator
        if participant_id != event.created_by:
            await self.notification_service.create_notification(
                user_id=event.created_by,
                title="New Participant",
                message=f"A new participant has joined your event '{event.title}'.",
                notification_type="participant_joined",
                data={
                    "event": event.to_dict(),
                    "participant_id": participant_id
                }
            )
        
        # Notify other participants
        for participant in event.participants:
            if participant.id not in [event.created_by, participant_id]:
                await self.notification_service.create_notification(
                    user_id=participant.id,
                    title="New Participant",
                    message=f"A new participant has joined the event '{event.title}'.",
                    notification_type="participant_joined",
                    data={
                        "event": event.to_dict(),
                        "participant_id": participant_id
                    }
                )
    
    async def notify_participant_left(
        self,
        event: Event,
        participant_id: str
    ) -> None:
        """Send notifications when a participant leaves an event."""
        # Notify event creator
        if participant_id != event.created_by:
            await self.notification_service.create_notification(
                user_id=event.created_by,
                title="Participant Left",
                message=f"A participant has left your event '{event.title}'.",
                notification_type="participant_left",
                data={
                    "event": event.to_dict(),
                    "participant_id": participant_id
                }
            )
        
        # Notify other participants
        for participant in event.participants:
            if participant.id not in [event.created_by, participant_id]:
                await self.notification_service.create_notification(
                    user_id=participant.id,
                    title="Participant Left",
                    message=f"A participant has left the event '{event.title}'.",
                    notification_type="participant_left",
                    data={
                        "event": event.to_dict(),
                        "participant_id": participant_id
                    }
                )
    
    async def notify_event_conflict(
        self,
        event: Event,
        conflicting_event: Event
    ) -> None:
        """Send notifications when an event conflict is detected."""
        # Notify both event creators
        for user_id in [event.created_by, conflicting_event.created_by]:
            await self.notification_service.create_notification(
                user_id=user_id,
                title="Event Conflict Detected",
                message=f"Your event '{event.title}' conflicts with another event.",
                notification_type="event_conflict",
                data={
                    "event": event.to_dict(),
                    "conflicting_event": conflicting_event.to_dict()
                }
            )
    
    async def _get_users_to_notify(self, event: Event) -> List[str]:
        """Get all users who should be notified about an event."""
        user_ids = set()
        
        # Add event creator
        user_ids.add(event.created_by)
        
        # Add participants
        for participant in event.participants:
            user_ids.add(participant.id)
        
        # Add users with shares
        stmt = select(EventShare).filter(EventShare.event_id == event.id)
        result = await self.session.execute(stmt)
        shares = result.scalars().all()
        for share in shares:
            user_ids.add(share.shared_with)
        
        return list(user_ids) 