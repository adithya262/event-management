from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "event_management",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.email",
        "app.tasks.reminders",
        "app.tasks.analytics"
    ]
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_max_tasks_per_child=1000,
)

# Periodic task scheduling
celery_app.conf.beat_schedule = {
    "check-upcoming-events": {
        "task": "app.tasks.reminders.check_upcoming_events",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
    "check-recurring-events": {
        "task": "app.tasks.reminders.check_recurring_events",
        "schedule": crontab(hour="*/1"),  # Every hour
    },
    "cleanup-old-events": {
        "task": "app.tasks.reminders.cleanup_old_events",
        "schedule": crontab(hour="0", minute="0"),  # Daily at midnight
    },
    "track-event-metrics": {
        "task": "app.tasks.analytics.track_event_metrics",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    "generate-weekly-reports": {
        "task": "app.tasks.analytics.generate_weekly_report",
        "schedule": crontab(hour="0", minute="0", day_of_week="monday"),  # Every Monday at midnight
    }
} 