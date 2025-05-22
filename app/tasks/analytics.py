from datetime import datetime, timedelta
from typing import Dict, List
from app.core.celery_app import celery_app
from app.models.event import Event, EventStatus
from app.models.user import User
from app.core.email import send_email

@celery_app.task(name="generate_event_report")
def generate_event_report(event_id: str, report_type: str = "summary") -> Dict:
    """Generate a report for a specific event."""
    event = Event.get(event_id)
    if not event:
        return {"error": "Event not found"}

    report_data = {
        "event_id": event.id,
        "title": event.title,
        "generated_at": datetime.utcnow().isoformat(),
        "report_type": report_type
    }

    if report_type == "summary":
        report_data.update({
            "total_participants": len(event.participants),
            "attendance_rate": event.calculate_attendance_rate(),
            "duration": (event.end_time - event.start_time).total_seconds() / 3600,
            "status": event.status.value
        })
    elif report_type == "detailed":
        report_data.update({
            "participants": [p.to_dict() for p in event.participants],
            "check_ins": event.get_check_in_data(),
            "feedback": event.get_feedback_data(),
            "resources_used": event.get_resource_usage()
        })

    return report_data

@celery_app.task(name="generate_weekly_report")
def generate_weekly_report(organization_id: str) -> None:
    """Generate a weekly report for all events in an organization."""
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    
    # Get all events in the past week
    events = Event.query.filter(
        Event.organization_id == organization_id,
        Event.start_time >= week_ago,
        Event.start_time <= now
    ).all()

    report_data = {
        "period": f"{week_ago.date()} to {now.date()}",
        "total_events": len(events),
        "events": []
    }

    for event in events:
        event_data = {
            "id": event.id,
            "title": event.title,
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat(),
            "participants": len(event.participants),
            "status": event.status.value
        }
        report_data["events"].append(event_data)

    # Send report to organization admins
    admins = User.query.filter(
        User.organization_id == organization_id,
        User.role == "admin"
    ).all()

    for admin in admins:
        send_email(
            email_to=admin.email,
            subject="Weekly Event Report",
            template_name="weekly_report.html",
            template_data=report_data
        )

@celery_app.task(name="track_event_metrics")
def track_event_metrics() -> None:
    """Track and update event metrics for analytics."""
    now = datetime.utcnow()
    active_events = Event.query.filter(
        Event.is_active == True,
        Event.start_time <= now,
        Event.end_time >= now
    ).all()

    for event in active_events:
        metrics = {
            "current_participants": len(event.participants),
            "check_in_rate": event.calculate_check_in_rate(),
            "resource_usage": event.get_resource_usage(),
            "last_updated": now.isoformat()
        }
        
        # Update event metrics in the database
        event.update_metrics(metrics) 