"""FastAPI gateway for the MailMind local demo."""

import json
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.tools.gmail import GmailToolManager
from backend.tools.calendar import CalendarToolManager
from backend.memory.store import MemoryManager

app = FastAPI(
    title="MailMind Agent API",
    description="Local demo API for the MailMind productivity assistant prototype.",
    version="0.1.0",
)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

gmail_manager = GmailToolManager()
calendar_manager = CalendarToolManager()
memory_manager = MemoryManager()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    thread_id: Optional[str] = Field(default="local-demo", max_length=128)


class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    feedback: Optional[str] = None


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "MailMind API",
        "version": app.version,
        "mode": "local_demo",
        "integrations": "mock",
    }


@app.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):
    """Stream a clearly labeled local-demo response using fixture data."""

    async def event_generator():
        yield _sse_event(
            {
                "type": "trace",
                "stage": "demo",
                "message": "Preparing the local demo response; no live account is connected.",
            }
        )
        emails = gmail_manager.search_emails("is:unread")
        events = calendar_manager.list_upcoming_events()
        response_payload = {
            "type": "content",
            "text": (
                "Local demo only: this response uses sample Gmail and Calendar fixtures, "
                "not your personal accounts. Live integrations, AI planning, and action "
                "execution are not configured in this prototype."
            ),
            "query": request.message,
            "citations": [
                *[
                    {
                        "source": "Gmail (sample)",
                        "title": email.get("subject", "Sample email"),
                        "timestamp": email.get("date", ""),
                        "snippet": email.get("snippet", ""),
                    }
                    for email in emails
                    if "error" not in email
                ],
                *[
                    {
                        "source": "Calendar (sample)",
                        "title": event.get("summary", "Sample event"),
                        "timestamp": event.get("start", ""),
                        "snippet": event.get("description", ""),
                    }
                    for event in events
                    if "error" not in event
                ],
            ],
        }
        yield _sse_event(response_payload)
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/v1/chat/approve")
async def approve_action(request: ApprovalRequest):
    """Reject action execution until resumable HITL and live integrations exist."""
    raise HTTPException(
        status_code=501,
        detail="Action approval is not implemented; no action was executed.",
    )


@app.get("/api/v1/memory")
async def get_memories():
    """Return persisted preferences only when a memory store is configured."""
    prefs = await memory_manager.get_user_preferences("local-demo")
    return {
        "configured": memory_manager.db is not None,
        "preferences": prefs,
    }


def _sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
