"""
MailMind Google Calendar Tool Suite
Encapsulates Google Calendar API v3 operations into LangChain tools.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class CalendarToolManager:
    """Manages Google Calendar operations for an authenticated user."""

    def __init__(self, service=None):
        self.service = service

    def list_upcoming_events(self, days_ahead: int = 7, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """List upcoming events for the primary calendar."""
        if not self.service:
            # Mock calendar data for development/offline testing
            now = datetime.now()
            return [
                {
                    "id": "mock_event_1",
                    "summary": "Technical Interview - Stripe",
                    "start": (now + timedelta(days=2)).replace(hour=16, minute=0).isoformat(),
                    "end": (now + timedelta(days=2)).replace(hour=17, minute=0).isoformat(),
                    "description": "System architecture and backend interview via Google Meet.",
                    "hangout_link": "https://meet.google.com/abc-defg-hij",
                    "is_sample": True,
                },
                {
                    "id": "mock_event_2",
                    "summary": "Weekly 1:1 with Mentor",
                    "start": (now + timedelta(days=3)).replace(hour=11, minute=0).isoformat(),
                    "end": (now + timedelta(days=3)).replace(hour=11, minute=30).isoformat(),
                    "description": "Progress check-in on project milestones.",
                    "is_sample": True,
                }
            ]

        try:
            now = datetime.utcnow().isoformat() + "Z"
            time_max = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"

            params = {
                "calendarId": "primary",
                "timeMin": now,
                "timeMax": time_max,
                "singleEvents": True,
                "orderBy": "startTime"
            }
            if query:
                params["q"] = query

            events_result = self.service.events().list(**params).execute()
            items = events_result.get("items", [])

            events = []
            for item in items:
                start = item.get("start", {}).get("dateTime", item.get("start", {}).get("date"))
                end = item.get("end", {}).get("dateTime", item.get("end", {}).get("date"))
                events.append({
                    "id": item.get("id"),
                    "summary": item.get("summary", "Untitled Event"),
                    "start": start,
                    "end": end,
                    "description": item.get("description", ""),
                    "hangout_link": item.get("hangoutLink", None)
                })
            return events
        except Exception as e:
            logger.exception("Error reading Google Calendar")
            raise RuntimeError("Google Calendar event lookup failed.") from e

    def check_availability(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """Checks if a specified time slot is free or conflicts with existing meetings."""
        raise NotImplementedError("Calendar availability checks are not implemented.")
