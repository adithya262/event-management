from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from app.models.event import Event, EventStatus, RecurrencePattern
from app.models.event_share import EventShare, SharePermission
from app.core.transaction import transaction_scope
from app.core.conflict_resolution import ConflictResolver
from app.services.changelog import ChangelogService
from app.models.event_version import EventVersion
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

class EventService:
    """Service for handling event operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conflict_resolver = ConflictResolver(session)
        self.changelog_service = ChangelogService(session)
    
    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        created_by: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        max_participants: Optional[int] = None,
        is_private: bool = False,
        recurrence_pattern: RecurrencePattern = RecurrencePattern.NONE,
        recurrence_end_date: Optional[datetime] = None,
        recurrence_interval: int = 1,
        recurrence_days: Optional[List[str]] = None,
        recurrence_exceptions: Optional[List[str]] = None
    ) -> Tuple[Event, List[Event]]:
        """Create a new event with optional recurrence."""
        async with transaction_scope(self.session) as transaction:
            # Create main event
            event = Event(
                title=title,
                start_time=start_time,
                end_time=end_time,
                created_by=created_by,
                description=description,
                location=location,
                max_participants=max_participants,
                is_private=is_private,
                recurrence_pattern=recurrence_pattern,
                recurrence_end_date=recurrence_end_date,
                recurrence_interval=recurrence_interval,
                recurrence_days=recurrence_days,
                recurrence_exceptions=recurrence_exceptions
            )
            
            # Check for conflicts
            conflicts = await self._check_conflicts(event)
            if conflicts:
                raise ValueError(f"Event conflicts with {len(conflicts)} existing events")
            
            # Add event to session
            self.session.add(event)
            await self.session.flush()
            
            # Generate recurring instances if needed
            instances = []
            if recurrence_pattern != RecurrencePattern.NONE:
                instances = event.get_recurring_instances()
                for instance in instances:
                    instance.id = None  # Let the database generate new IDs
                    self.session.add(instance)
            
            # Add to transaction
            await transaction.add_operation(
                "create_event",
                "event",
                event.id,
                event.to_dict()
            )
            
            return event, instances
    
    async def update_event(
        self,
        event_id: str,
        updates: Dict[str, Any],
        user_id: str
    ) -> Event:
        """Update an existing event."""
        async with transaction_scope(self.session) as transaction:
            # Get event
            event = await self.session.get(Event, event_id)
            if not event:
                raise ValueError("Event not found")
            
            # Check permissions
            if not await self._check_permission(event_id, user_id, "edit_details"):
                raise PermissionError("User does not have permission to edit this event")
            
            # Store previous state for versioning
            previous_state = event.to_dict()
            
            # Update fields
            for key, value in updates.items():
                if hasattr(event, key):
                    setattr(event, key, value)
            
            # Check for conflicts
            conflicts = await self._check_conflicts(event)
            if conflicts:
                raise ValueError(f"Update would create conflicts with {len(conflicts)} existing events")
            
            # Create version record
            await self.changelog_service.create_version(
                "event",
                event_id,
                updates,
                previous_state,
                event.to_dict(),
                user_id
            )
            
            # Add to transaction
            await transaction.add_operation(
                "update_event",
                "event",
                event_id,
                updates
            )
            
            return event
    
    async def delete_event(self, event_id: str, user_id: str) -> bool:
        """Delete an event."""
        async with transaction_scope(self.session) as transaction:
            # Get event
            event = await self.session.get(Event, event_id)
            if not event:
                raise ValueError("Event not found")
            
            # Check permissions
            if not await self._check_permission(event_id, user_id, "delete"):
                raise PermissionError("User does not have permission to delete this event")
            
            # Add to transaction
            await transaction.add_operation(
                "delete_event",
                "event",
                event_id,
                event.to_dict()
            )
            
            # Delete event
            await self.session.delete(event)
            return True
    
    async def get_event(self, event_id: str, user_id: str) -> Event:
        """Get an event by ID."""
        event = await self.session.get(Event, event_id)
        if not event:
            raise ValueError("Event not found")
        
        # Check permissions
        if not await self._check_permission(event_id, user_id, "view"):
            raise PermissionError("User does not have permission to view this event")
        
        return event
    
    async def list_events(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[EventStatus] = None,
        include_private: bool = False
    ) -> List[Event]:
        """List events with various filters."""
        stmt = select(Event)
        # Apply filters
        if start_date:
            stmt = stmt.filter(Event.start_time >= start_date)
        if end_date:
            stmt = stmt.filter(Event.end_time <= end_date)
        if status:
            stmt = stmt.filter(Event.status == status)
        # Handle privacy
        if not include_private:
            stmt = stmt.filter(
                or_(
                    Event.is_private == False,
                    Event.created_by == user_id,
                    Event.id.in_(
                        select(EventShare.event_id).filter(EventShare.shared_with == user_id)
                    )
                )
            )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def batch_create_events(
        self,
        events_data: List[Dict[str, Any]],
        created_by: str
    ) -> List[Event]:
        """Create multiple events in a single transaction."""
        created_events = []
        
        async with transaction_scope(self.session) as transaction:
            for event_data in events_data:
                event, instances = await self.create_event(
                    created_by=created_by,
                    **event_data
                )
                created_events.extend([event] + instances)
            
            # Add batch operation to transaction
            await transaction.add_operation(
                "batch_create_events",
                "event",
                "batch",
                {"count": len(created_events)}
            )
        
        return created_events
    
    async def _check_conflicts(self, event: Event) -> List[Event]:
        """Check for conflicts with existing events."""
        stmt = select(Event).filter(
            and_(
                Event.id != event.id,
                Event.status != EventStatus.CANCELLED,
                or_(
                    and_(
                        Event.start_time <= event.start_time,
                        Event.end_time > event.start_time
                    ),
                    and_(
                        Event.start_time < event.end_time,
                        Event.end_time >= event.end_time
                    ),
                    and_(
                        Event.start_time >= event.start_time,
                        Event.end_time <= event.end_time
                    )
                )
            )
        )
        result = await self.session.execute(stmt)
        conflicting_events = result.scalars().all()
        return [e for e in conflicting_events if event.check_conflict(e)]
    
    async def _check_permission(
        self,
        event_id: str,
        user_id: str,
        action: str
    ) -> bool:
        """Check if a user has permission to perform an action on an event."""
        # Get event
        event = await self.session.get(Event, event_id)
        if not event:
            return False
        # Creator has all permissions
        if event.created_by == user_id:
            return True
        # Check share permissions
        stmt = select(EventShare).filter(
            and_(
                EventShare.event_id == event_id,
                EventShare.shared_with == user_id
            )
        )
        result = await self.session.execute(stmt)
        share = result.scalars().first()
        if not share:
            return False
        return share.can_perform_action(action) 

    async def get_event_shares(
        self,
        event_id: str,
        user_id: str
    ) -> List[EventShare]:
        """Get all shares for a given event, with permission check."""
        # Check if user has permission to view shares (owner or manage permission)
        if not await self._check_permission(event_id, user_id, "view_shares") and not await self._check_permission(event_id, user_id, "manage"): # Assuming 'view_shares' or 'manage' permission is needed
             raise PermissionError("User does not have permission to view shares for this event")

        stmt = select(EventShare).filter(EventShare.event_id == event_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_event_share(
        self,
        event_id: str,
        target_user_id: str,
        permission: SharePermission,
        user_id: str
    ) -> Optional[EventShare]:
        """Update the permission level for a specific user on an event, with permission check."""
        # Check if user has permission to manage shares (owner or manage permission)
        if not await self._check_permission(event_id, user_id, "manage"):
            raise PermissionError("User does not have permission to manage shares for this event")

        stmt = select(EventShare).filter(
            and_(
                EventShare.event_id == event_id,
                EventShare.shared_with == target_user_id # Corrected to shared_with
            )
        )
        result = await self.session.execute(stmt)
        share = result.scalars().first()

        if not share:
            raise ValueError("Share not found for this user on this event")

        share.permission = permission
        await self.session.commit()
        await self.session.refresh(share)
        return share

    async def delete_event_share(
        self,
        event_id: str,
        target_user_id: str,
        user_id: str
    ) -> bool:
        """Remove a user's share for an event, with permission check."""
        # Check if user has permission to manage shares (owner or manage permission)
        if not await self._check_permission(event_id, user_id, "manage"):
            raise PermissionError("User does not have permission to manage shares for this event")

        stmt = select(EventShare).filter(
            and_(
                EventShare.event_id == event_id,
                EventShare.shared_with == target_user_id # Corrected to shared_with
            )
        )
        result = await self.session.execute(stmt)
        share = result.scalars().first()

        if not share:
            raise ValueError("Share not found for this user on this event")

        await self.session.delete(share)
        await self.session.commit()
        return True

    async def rollback_event(
        self,
        event_id: str,
        version_id: int,
        user_id: str
    ) -> Event:
        """Rollback an event to a specific version."""
        async with transaction_scope(self.session) as transaction:
            # Get event
            event = await self.session.get(Event, event_id)
            if not event:
                raise ValueError("Event not found")

            # Check permissions (assuming 'rollback' is a valid action)
            if not await self._check_permission(event_id, user_id, "rollback") and not await self._check_permission(event_id, user_id, "manage"): # Assuming 'rollback' or 'manage' permission is needed
                 raise PermissionError("User does not have permission to rollback this event")

            # Get the target version
            stmt = select(EventVersion).filter(
                and_(
                    EventVersion.event_id == event_id,
                    EventVersion.version == version_id
                )
            )
            result = await self.session.execute(stmt)
            version_to_apply = result.scalars().first()

            if not version_to_apply:
                raise ValueError(f"Version {version_id} not found for event {event_id}")

            # Apply changes from the version. Note: This simplistic approach overwrites fields.
            # A more sophisticated approach might apply changes based on the diff in the version record.
            # For now, assuming the 'changes' dict in EventVersion contains the state to apply.
            # *** You may need to adjust this logic based on how your EventVersion.changes is structured ***
            updates_to_apply = version_to_apply.changes

            # Apply updates to the event
            for key, value in updates_to_apply.items():
                if hasattr(event, key):
                    setattr(event, key, value)

            # Check for conflicts after rollback
            conflicts = await self._check_conflicts(event)
            if conflicts:
                 # Decide how to handle conflicts on rollback - potentially raise error or attempt resolution
                 raise ValueError(f"Rollback to version {version_id} would create conflicts") # Raising error for simplicity

            # Create a new version recording the rollback
            # This creates a version for the current state AFTER the rollback
            await self.changelog_service.create_version(
                 "event",
                 event_id,
                 {"rolled_back_to_version": version_id}, # Record the rollback action
                 event.to_dict(), # Previous state is the state before this rollback
                 event.to_dict(), # Current state is the state after applying the version
                 user_id
             )

            # Add to transaction
            await transaction.add_operation(
                "rollback_event",
                "event",
                event_id,
                {"rolled_back_to_version": version_id}
            )

            await self.session.commit()
            await self.session.refresh(event)

            return event

    async def get_event_version(
        self,
        event_id: str,
        version_id: int,
        user_id: str # Include user_id for permission check
    ) -> EventVersion:
        """Get a specific event version by event ID and version ID."""
        # Check if the user has permission to view the event (and thus its versions)
        # Reuse the get_event permission logic as versions are tied to the event
        await self.get_event(event_id, user_id) # This will raise an exception if event not found or no view permission

        stmt = select(EventVersion).filter(
            and_(
                EventVersion.event_id == event_id,
                EventVersion.version == version_id
            )
        )
        result = await self.session.execute(stmt)
        version = result.scalars().first()

        if not version:
            raise ValueError(f"Version {version_id} not found for event {event_id}")

        return version 

    async def add_participant(self, event_id: str, user_id: str) -> bool:
        """Add a participant to an event."""
        async with transaction_scope(self.session) as transaction:
            # Get event
            event = await self.session.get(Event, event_id)
            if not event:
                raise ValueError("Event not found")

            # Check if event is full
            if event.max_participants and len(event.participants) >= event.max_participants:
                raise ValueError("Event is full")

            # Check if user is already a participant
            if user_id in [p.id for p in event.participants]:
                raise ValueError("User is already a participant")

            # Add participant
            event.participants.append(await self.session.get(User, user_id))
            await self.session.flush()

            # Add to transaction
            await transaction.add_operation(
                "add_participant",
                "event",
                event_id,
                {"user_id": user_id}
            )

            return True

    async def remove_participant(self, event_id: str, user_id: str) -> bool:
        """Remove a participant from an event."""
        async with transaction_scope(self.session) as transaction:
            # Get event
            event = await self.session.get(Event, event_id)
            if not event:
                raise ValueError("Event not found")

            # Check if user is a participant
            if user_id not in [p.id for p in event.participants]:
                raise ValueError("User is not a participant")

            # Remove participant
            event.participants.remove(await self.session.get(User, user_id))
            await self.session.flush()

            # Add to transaction
            await transaction.add_operation(
                "remove_participant",
                "event",
                event_id,
                {"user_id": user_id}
            )

            return True

    async def check_event_conflicts(self, event: Event) -> List[Event]:
        """Check for conflicts with existing events."""
        return await self._check_conflicts(event) 