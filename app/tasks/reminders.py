from datetime import datetime, timedelta
from typing import List
from app.core.celery_app import celery_app
from app.models.event import Event, EventStatus
from app.tasks.email import send_event_reminder

@celery_app.task(name="schedule_event_reminders")
def schedule_event_reminders(event_id: str) -> None:
    """Schedule reminder emails for an event at different intervals."""
    event = Event.get(event_id)
    if not event:
        return

    # Get all participant emails
    participant_emails = [p.email for p in event.participants]
    
    # Schedule reminders at different intervals
    reminder_intervals = [7, 3, 1]  # 7 days, 3 days, and 1 day before
    
    for days in reminder_intervals:
        reminder_date = event.start_time - timedelta(days=days)
        if reminder_date > datetime.utcnow():
            send_event_reminder.apply_async(
                args=[event_id, participant_emails, days],
                eta=reminder_date
            )

@celery_app.task(name="check_upcoming_events")
def check_upcoming_events() -> None:
    """Check for events starting in the next 24 hours and send immediate reminders."""
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)
    
    # Find events starting in the next 24 hours
    upcoming_events = Event.query.filter(
        Event.start_time >= now,
        Event.start_time <= tomorrow,
        Event.is_active == True
    ).all()
    
    for event in upcoming_events:
        participant_emails = [p.email for p in event.participants]
        send_event_reminder.delay(
            event_id=event.id,
            recipient_emails=participant_emails,
            days_before=0  # Immediate reminder
        )

@celery_app.task(name="check_recurring_events")
def check_recurring_events() -> None:
    """Check and create instances for recurring events."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        # Get active recurring events
        events = db.query(Event).filter(
            Event.recurrence_pattern != "none",
            Event.is_active == True
        ).all()

        for event in events:
            # Generate instances for the next 30 days
            instances = event.get_recurring_instances()
            for instance in instances:
                if instance.start_time > datetime.utcnow():
                    db.add(instance)
        
        db.commit()
    finally:
        db.close()

@celery_app.task(name="cleanup_old_events")
def cleanup_old_events() -> None:
    """Clean up old completed events."""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        # Archive events completed more than 30 days ago
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        old_events = db.query(Event).filter(
            Event.end_time < thirty_days_ago,
            Event.status == EventStatus.COMPLETED
        ).all()

        for event in old_events:
            event.is_active = False
        
        db.commit()
    finally:
        db.close() 