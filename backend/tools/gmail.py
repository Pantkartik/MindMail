"""
MailMind Gmail Tool Suite
Encapsulates Google Gmail API v1 operations into LangChain tools.
"""

import base64
import logging
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def parse_email_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to parse a raw Gmail API message dict into clean fields."""
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    
    body = ""
    payload = msg.get("payload", {})
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                break
    elif "data" in payload.get("body", {}):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    
    return {
        "id": msg.get("id"),
        "thread_id": msg.get("threadId"),
        "sender": headers.get("from", "Unknown"),
        "to": headers.get("to", "Unknown"),
        "subject": headers.get("subject", "No Subject"),
        "date": headers.get("date", ""),
        "snippet": msg.get("snippet", ""),
        "body": body[:2000]  # Truncate for prompt efficiency
    }


class GmailToolManager:
    """Manages Gmail service instances per authenticated user."""
    
    def __init__(self, service=None):
        self.service = service

    def search_emails(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search emails using Gmail query syntax (e.g. 'is:unread from:company')."""
        if not self.service:
            # Return realistic mock structure for test / offline mode
            return [{
                "id": "mock_email_001",
                "thread_id": "mock_thread_001",
                "sender": "recruiter@techcorp.io",
                "to": "user@mailmind.ai",
                "subject": "Interview Invitation: Senior Software Engineer",
                "date": "2026-10-01T10:00:00Z",
                "snippet": "We would like to invite you for a 45-min system design interview...",
                "body": "Dear Candidate,\nWe would like to invite you for a 45-minute technical interview next week...",
                "is_sample": True,
            }]
        
        try:
            results = self.service.users().messages().list(
                userId="me", q=query, maxResults=max_results
            ).execute()
            messages = results.get("messages", [])
            parsed_list = []
            for m in messages:
                detail = self.service.users().messages().get(
                    userId="me", id=m["id"], format="full"
                ).execute()
                parsed_list.append(parse_email_message(detail))
            return parsed_list
        except Exception as e:
            logger.exception("Error querying Gmail API")
            raise RuntimeError("Gmail search failed.") from e

    def draft_reply(self, thread_id: str, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Drafts an email for user review and approval (HITL)."""
        return {
            "status": "draft_prepared",
            "thread_id": thread_id,
            "to": to,
            "subject": subject if subject.startswith("Re:") else f"Re: {subject}",
            "body": body,
            "persisted": False,
            "requires_approval": True,
        }

    def send_email(self, to: str, subject: str, body: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Executes actual email dispatch (Invoked ONLY after user approval)."""
        if not self.service:
            raise RuntimeError("Gmail is not configured; no email was sent.")
        
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        body_payload = {"raw": raw}
        if thread_id:
            body_payload["threadId"] = thread_id
            
        sent = self.service.users().messages().send(userId="me", body=body_payload).execute()
        return {"status": "sent", "id": sent.get("id")}
