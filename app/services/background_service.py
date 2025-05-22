from typing import List, Dict, Any, Optional
from fastapi import BackgroundTasks
from app.tasks.email import send_event_invitation, send_event_reminder, send_event_update
from app.tasks.reminders import schedule_event_reminders, check_recurring_events, cleanup_old_events

class BackgroundService:
    def __init__(self, background_tasks: BackgroundTasks):
        self.background_tasks = background_tasks

    def send_event_invitations(
        self,
        event_id: str,
        user_ids: List[str],
        template_data: Dict[str, Any]
    ) -> None:
        """Send event invitations using Celery task."""
        send_event_invitation.delay(event_id, user_ids, template_data)

    def send_event_reminder(
        self,
        event_id: str,
        reminder_type: str = "24h"
    ) -> None:
        """Send event reminder using Celery task."""
        send_event_reminder.delay(event_id, reminder_type)

    def send_event_update(
        self,
        event_id: str,
        update_type: str,
        changes: Dict[str, Any]
    ) -> None:
        """Send event update using Celery task."""
        send_event_update.delay(event_id, update_type, changes)

    def schedule_reminders(self) -> None:
        """Schedule event reminders using Celery task."""
        schedule_event_reminders.delay()

    def check_recurring_events(self) -> None:
        """Check recurring events using Celery task."""
        check_recurring_events.delay()

    def cleanup_old_events(self) -> None:
        """Clean up old events using Celery task."""
        cleanup_old_events.delay()

    def add_light_task(self, func: callable, *args, **kwargs) -> None:
        """Add a light task to be executed in the background using FastAPI's BackgroundTasks."""
        self.background_tasks.add_task(func, *args, **kwargs) 