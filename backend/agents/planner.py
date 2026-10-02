"""
MailMind AI Planner
Decomposes high-level user queries into multi-agent task execution plans.
"""

from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.chat_models import init_chat_model
from backend.agents.state import MailMindState, PlanStep


class PlanStepSchema(BaseModel):
    step_id: int = Field(description="Order of execution starting at 1")
    tool: Literal["gmail", "calendar", "rag", "memory"] = Field(
        description="Specialized sub-agent or tool domain to invoke"
    )
    action: str = Field(description="Action name, e.g., 'search_emails', 'check_calendar', 'retrieve_rag'")
    args: Dict[str, Any] = Field(description="Arguments required for the action execution")
    rationale: str = Field(description="Explanation of why this step is needed")


class ExecutionPlan(BaseModel):
    plan_summary: str = Field(description="High level summary of the strategy to solve the user query")
    steps: List[PlanStepSchema] = Field(description="Sequential list of atomic tasks")


PLANNER_SYSTEM_PROMPT = """You are the Lead Task Planner for MailMind, an agentic personal productivity assistant.
Your goal is to inspect the user's inquiry, review any active user preferences, and decompose the question into a structured, step-by-step task plan.

Available Tools / Sub-Agents:
1. `gmail`: Real-time query to Gmail API (e.g. search unread emails, search by sender or label, fetch thread).
2. `calendar`: Search upcoming events, check schedule conflicts, or get agenda details.
3. `rag`: Hybrid semantic vector search over past email knowledge base.
4. `memory`: Retrieve user preferences, past habits, or entity relations.

Rules:
- If the question asks about future schedule, meetings, or availability, schedule a `calendar` check.
- If the question requires details from past emails or communications, use `gmail` or `rag`.
- If an email draft or reply is needed, plan the search first, draft the reply, and mark that it will need human approval.
- Ensure the steps are ordered logically so later steps can use evidence gathered by earlier steps.
"""


def create_planner_node(model_name: str = "openai:gpt-4o"):
    """Creates the planner node callable."""
    llm = init_chat_model(model_name, temperature=0.0)
    structured_planner = llm.with_structured_output(ExecutionPlan)

    def planner_node(state: MailMindState) -> Dict[str, Any]:
        user_query = state["messages"][-1].content
        user_prefs = state.get("user_preferences", {})

        prompt_input = (
            f"User Query: {user_query}\n"
            f"Active User Preferences: {user_prefs}"
        )

        plan_result: ExecutionPlan = structured_planner.invoke([
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=prompt_input)
        ])

        steps: List[PlanStep] = [
            {
                "step_id": step.step_id,
                "tool": step.tool,
                "action": step.action,
                "args": step.args,
                "status": "pending",
                "result": None,
            }
            for step in plan_result.steps
        ]

        return {
            "plan": steps,
            "current_step_index": 0,
            "needs_replanning": False,
        }

    return planner_node
