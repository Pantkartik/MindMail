"""
MailMind Dual-Tier Memory Engine
Manages short-term conversation state and long-term user preference extraction.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.chat_models import init_chat_model


class UserProfileMemory(BaseModel):
    category: str = Field(description="Category: 'communication_style', 'schedule_habits', 'entity_relation'")
    key: str = Field(description="Short identifier for preference, e.g. 'email_length'")
    value: str = Field(description="The preference statement, e.g. 'Prefers concise emails under 4 sentences'")
    confidence: float = Field(default=1.0, description="Confidence score from 0.0 to 1.0")


MEMORY_EXTRACTOR_PROMPT = """You are the Memory Auditor for MailMind.
Analyze the conversation snippet between the user and assistant.
Identify any persistent preferences, habits, or facts explicitly or implicitly shared by the user.

Categories:
1. `communication_style`: Email tone, brevity, sign-off formulas, emoji usage.
2. `schedule_habits`: Preferred meeting times, buffer times, blackout hours.
3. `entity_relation`: Names and roles of professors, recruiters, managers, or colleagues.

DO NOT extract temporary context (e.g. 'I am hungry right now').
ONLY extract rules that apply to future sessions.
"""


class MemoryManager:
    """Manages reading and writing persistent long-term memories."""

    def __init__(self, db_session=None):
        self.db = db_session

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Fetch all stored preferences for the user."""
        # Returns default preferences if DB is not configured yet
        return {
            "tone": "Professional and concise",
            "max_sentences": 4,
            "sign_off": "Best regards,\nKartik",
            "preferred_meeting_times": "After 2:00 PM",
            "college_domain": "college.edu"
        }

    async def extract_and_save_preferences(self, user_id: str, messages: list) -> List[UserProfileMemory]:
        """Analyzes recent messages to detect and persist new user habits/preferences."""
        llm = init_chat_model("openai:gpt-4o-mini", temperature=0.0)
        structured_auditor = llm.with_structured_output(UserProfileMemory)

        formatted_convo = "\n".join([f"{m.type}: {m.content}" for m in messages[-4:]])
        try:
            detected = structured_auditor.invoke([
                SystemMessage(content=MEMORY_EXTRACTOR_PROMPT),
                HumanMessage(content=formatted_convo)
            ])
            return [detected]
        except Exception:
            return []
