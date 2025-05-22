from celery.schedules import crontab
from app.core.celery_app import celery_app
from app.tasks.reminders import schedule_event_reminders, check_recurring_events, cleanup_old_events

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'schedule-event-reminders': {
        'task': 'app.tasks.reminders.schedule_event_reminders',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'check-recurring-events': {
        'task': 'app.tasks.reminders.check_recurring_events',
        'schedule': crontab(hour='*/1'),  # Every hour
    },
    'cleanup-old-events': {
        'task': 'app.tasks.reminders.cleanup_old_events',
        'schedule': crontab(hour='0', minute='0'),  # Daily at midnight
    },
} 