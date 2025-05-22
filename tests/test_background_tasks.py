import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app.tasks.email import send_event_invitation, send_event_reminder, send_event_update
from app.tasks.reminders import schedule_event_reminders, check_upcoming_events
from app.tasks.analytics import generate_event_report, generate_weekly_report, track_event_metrics
from app.models.event import Event, EventStatus
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
def mock_event():
    event = MagicMock(spec=Event)
    event.id = "test-event-id"
    event.title = "Test Event"
    event.start_time = datetime.utcnow() + timedelta(days=1)
    event.end_time = datetime.utcnow() + timedelta(days=1, hours=2)
    event.status = EventStatus.SCHEDULED
    event.participants = []
    event.calculate_attendance_rate.return_value = 0.8
    event.calculate_check_in_rate.return_value = 0.75
    event.get_resource_usage.return_value = {"cpu": 50, "memory": 60}
    event.get_check_in_data.return_value = []
    event.get_feedback_data.return_value = []
    event.to_dict.return_value = {
        "id": event.id,
        "title": event.title,
        "start_time": event.start_time.isoformat(),
        "end_time": event.end_time.isoformat(),
        "status": event.status.value
    }
    return event

@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = "test-user-id"
    user.email = "test@example.com"
    user.role = "admin"
    user.organization_id = "test-org-id"
    return user

@pytest.mark.asyncio
@patch("app.tasks.email.send_email")
@patch("app.models.event.Event.get")
def test_send_event_invitation(session: AsyncSession, mock_get_event, mock_send_email, mock_event):
    mock_get_event.return_value = mock_event
    recipient_emails = ["user1@example.com", "user2@example.com"]
    
    send_event_invitation(mock_event.id, recipient_emails)
    
    assert mock_send_email.call_count == 2
    mock_send_email.assert_any_call(
        email_to="user1@example.com",
        subject=f"Invitation: {mock_event.title}",
        template_name="event_invitation.html",
        template_data={
            "event": mock_event.to_dict(),
            "recipient_email": "user1@example.com"
        }
    )

@pytest.mark.asyncio
@patch("app.tasks.email.send_email")
@patch("app.models.event.Event.get")
def test_send_event_reminder(session: AsyncSession, mock_get_event, mock_send_email, mock_event):
    mock_get_event.return_value = mock_event
    recipient_emails = ["user1@example.com"]
    days_before = 1
    
    send_event_reminder(mock_event.id, recipient_emails, days_before)
    
    mock_send_email.assert_called_once_with(
        email_to="user1@example.com",
        subject=f"Reminder: {mock_event.title} in {days_before} days",
        template_name="event_reminder.html",
        template_data={
            "event": mock_event.to_dict(),
            "days_before": days_before,
            "recipient_email": "user1@example.com"
        }
    )

@pytest.mark.asyncio
@patch("app.models.event.Event.get")
def test_generate_event_report(session: AsyncSession, mock_get_event, mock_event):
    mock_get_event.return_value = mock_event
    
    # Test summary report
    summary_report = generate_event_report(mock_event.id, "summary")
    assert summary_report["event_id"] == mock_event.id
    assert summary_report["report_type"] == "summary"
    assert "total_participants" in summary_report
    assert "attendance_rate" in summary_report
    
    # Test detailed report
    detailed_report = generate_event_report(mock_event.id, "detailed")
    assert detailed_report["event_id"] == mock_event.id
    assert detailed_report["report_type"] == "detailed"
    assert "participants" in detailed_report
    assert "check_ins" in detailed_report
    assert "feedback" in detailed_report
    assert "resources_used" in detailed_report

@pytest.mark.asyncio
@patch("app.tasks.analytics.send_email")
@patch("app.models.user.User.query")
@patch("app.models.event.Event.query")
def test_generate_weekly_report(session: AsyncSession, mock_event_query, mock_user_query, mock_send_email, mock_event, mock_user):
    mock_event_query.filter.return_value.all.return_value = [mock_event]
    mock_user_query.filter.return_value.all.return_value = [mock_user]
    
    generate_weekly_report("test-org-id")
    
    mock_send_email.assert_called_once_with(
        email_to=mock_user.email,
        subject="Weekly Event Report",
        template_name="weekly_report.html",
        template_data={
            "period": f"{datetime.utcnow().date() - timedelta(days=7)} to {datetime.utcnow().date()}",
            "total_events": 1,
            "events": [mock_event.to_dict()]
        }
    )

@pytest.mark.asyncio
@patch("app.models.event.Event.query")
def test_track_event_metrics(session: AsyncSession, mock_event_query, mock_event):
    mock_event_query.filter.return_value.all.return_value = [mock_event]
    
    track_event_metrics()
    
    mock_event.update_metrics.assert_called_once_with({
        "current_participants": 0,
        "check_in_rate": 0.75,
        "resource_usage": {"cpu": 50, "memory": 60},
        "last_updated": datetime.utcnow().isoformat()
    }) 