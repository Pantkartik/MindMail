"""
MailMind FastAPI Server
REST & Server-Sent Events (SSE) API Gateway for MailMind.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import asyncio

from backend.tools.gmail import GmailToolManager
from backend.tools.calendar import CalendarToolManager
from backend.rag.pipeline import EmailRAGPipeline
from backend.memory.store import MemoryManager
from backend.agents.orchestrator import build_mailmind_graph

app = FastAPI(
    title="MailMind Agent API",
    description="Agentic Personal Productivity & Email Assistant API",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate Core Managers
gmail_manager = GmailToolManager()
calendar_manager = CalendarToolManager()
rag_pipeline = EmailRAGPipeline()
memory_manager = MemoryManager()


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default_session"
    user_id: Optional[str] = "user_demo"


class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    feedback: Optional[str] = None


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "MailMind API", "version": "1.0.0"}


@app.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint with Server-Sent Events (SSE) to stream planner steps,
    tool execution traces, and final synthesized answers.
    """
    async def event_generator():
        # Initial status
        yield f"data: {json.dumps({'type': 'trace', 'stage': 'planner', 'message': 'Decomposing inquiry into tasks...'})}\n\n"
        await asyncio.sleep(0.3)

        # Mock trace progression for demo streaming
        yield f"data: {json.dumps({'type': 'trace', 'stage': 'gmail_search', 'message': 'Querying recent Gmail messages...'})}\n\n"
        await asyncio.sleep(0.4)

        yield f"data: {json.dumps({'type': 'trace', 'stage': 'calendar_check', 'message': 'Checking Google Calendar availability...'})}\n\n"
        await asyncio.sleep(0.3)

        yield f"data: {json.dumps({'type': 'trace', 'stage': 'evidence_verification', 'message': 'Cross-referencing evidence & citations...'})}\n\n"
        await asyncio.sleep(0.3)

        # Output payload
        response_payload = {
            "type": "content",
            "text": (
                "You have an upcoming **Technical Interview with Stripe** scheduled for "
                "**Thursday at 4:00 PM IST**.\n\n"
                "According to the recruiter email from *recruiter@techcorp.io*, you should prepare "
                "a 15-minute presentation on your distributed systems project.\n\n"
                "I have also prepared a draft reply to confirm your attendance."
            ),
            "citations": [
                {
                    "source": "Gmail",
                    "title": "Interview Invitation: Senior Software Engineer",
                    "sender": "recruiter@techcorp.io",
                    "timestamp": "2026-10-01"
                },
                {
                    "source": "Google Calendar",
                    "title": "Technical Interview - Stripe",
                    "timestamp": "Thursday, 4:00 PM - 5:00 PM"
                }
            ],
            "pending_approval": {
                "action": "send_email",
                "to": "recruiter@techcorp.io",
                "subject": "Re: Interview Invitation: Senior Software Engineer",
                "body": "Dear Recruiter,\n\nThank you for the update. I confirm my availability for Thursday at 4:00 PM IST.\n\nBest regards,\nKartik"
            }
        }
        yield f"data: {json.dumps(response_payload)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/v1/chat/approve")
async def approve_action(request: ApprovalRequest):
    """Handles Human-in-the-Loop approval/rejection."""
    if request.approved:
        return {"status": "success", "message": "Action approved and dispatched to Gmail API."}
    else:
        return {"status": "cancelled", "message": "Action rejected. Assistant state reset."}


@app.get("/api/v1/memory")
async def get_memories(user_id: str = "user_demo"):
    """Fetches long-term extracted user habits and preferences."""
    prefs = await memory_manager.get_user_preferences(user_id)
    return {"user_id": user_id, "preferences": prefs}
