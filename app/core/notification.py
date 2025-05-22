from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

class NotificationService:
    """Service for handling notifications."""

    def __init__(self):
        self.notifications = []

    def create_notification(self, user_id: str, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new notification."""
        notification = {
            "id": str(uuid4()),
            "user_id": user_id,
            "message": message,
            "data": data or {},
            "created_at": datetime.utcnow().isoformat(),
            "read": False
        }
        self.notifications.append(notification)
        return notification

    def get_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all notifications for a user."""
        return [n for n in self.notifications if n["user_id"] == user_id]

    def mark_as_read(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Mark a notification as read."""
        for notification in self.notifications:
            if notification["id"] == notification_id:
                notification["read"] = True
                return notification
        return None 