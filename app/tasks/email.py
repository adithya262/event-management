from typing import List, Dict, Any, Optional
from app.core.celery_app import celery_app
from app.core.email import send_email
from app.models.event import Event
from app.models.user import User

@celery_app.task(name="send_event_invitation")
def send_event_invitation(
    event_id: str,
    recipient_emails: List[str],
    template_name: str = "event_invitation.html"
) -> None:
    """Send event invitation emails to multiple recipients."""
    event = Event.get(event_id)
    if not event:
        return
    
    for email in recipient_emails:
        send_email(
            email_to=email,
            subject=f"Invitation: {event.title}",
            template_name=template_name,
            template_data={
                "event": event.to_dict(),
                "recipient_email": email
            }
        )

@celery_app.task(name="send_event_reminder")
def send_event_reminder(
    event_id: str,
    recipient_emails: List[str],
    days_before: int,
    template_name: str = "event_reminder.html"
) -> None:
    """Send event reminder emails to participants."""
    event = Event.get(event_id)
    if not event:
        return
    
    for email in recipient_emails:
        send_email(
            email_to=email,
            subject=f"Reminder: {event.title} in {days_before} days",
            template_name=template_name,
            template_data={
                "event": event.to_dict(),
                "days_before": days_before,
                "recipient_email": email
            }
        )

@celery_app.task(name="send_event_update")
def send_event_update(
    event_id: str,
    recipient_emails: List[str],
    update_type: str,
    changes: dict,
    template_name: str = "event_update.html"
) -> None:
    """Send event update notifications to participants."""
    event = Event.get(event_id)
    if not event:
        return
    
    for email in recipient_emails:
        send_email(
            email_to=email,
            subject=f"Update: {event.title}",
            template_name=template_name,
            template_data={
                "event": event.to_dict(),
                "update_type": update_type,
                "changes": changes,
                "recipient_email": email
            }
        ) 