"""
MailMind Multi-Agent Orchestrator
Builds the LangGraph state machine coordinating Planner, Sub-Agents, Verifier, and HITL Interrupts.
"""

from typing import Dict, Any, Literal
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command

from backend.agents.state import MailMindState, PlanStep, CitationSource
from backend.agents.planner import create_planner_node
from backend.tools.gmail import GmailToolManager
from backend.tools.calendar import CalendarToolManager
from backend.rag.pipeline import EmailRAGPipeline
from backend.memory.store import MemoryManager


SYNTHESIZER_PROMPT = """You are MailMind, an executive personal email and schedule assistant.
You have retrieved the following pieces of evidence:
- Emails: {emails}
- Calendar Events: {events}
- Past Memories / Preferences: {memories}

Your Task:
Synthesize an authoritative, helpful response directly answering the user's inquiry.
Adhere strictly to user preferences:
- Tone: {tone}
- Max length: {max_length}

If you recommend taking an action (such as drafting an email response or booking a calendar invite), produce the draft clearly and state that user approval is required before execution.
Always cite your evidence clearly.
"""


def build_mailmind_graph(
    gmail_mgr: GmailToolManager,
    calendar_mgr: CalendarToolManager,
    rag_pipe: EmailRAGPipeline,
    memory_mgr: MemoryManager,
    model_name: str = "openai:gpt-4o"
):
    """Assembles and compiles the full MailMind LangGraph workflow."""
    builder = StateGraph(MailMindState)
    llm = init_chat_model(model_name, temperature=0.2)

    # 1. Planner Node
    planner_fn = create_planner_node(model_name)
    builder.add_node("planner", planner_fn)

    # 2. Tool Execution Node
    def tool_executor(state: MailMindState) -> Dict[str, Any]:
        plan = state.get("plan", [])
        retrieved_emails = list(state.get("retrieved_emails", []))
        retrieved_events = list(state.get("retrieved_events", []))
        retrieved_memories = list(state.get("retrieved_memories", []))
        citations = list(state.get("citations", []))
        pending_action = None

        for step in plan:
            if step["status"] == "completed":
                continue

            tool_name = step["tool"]
            action = step["action"]
            args = step.get("args", {})

            if tool_name == "gmail":
                if action == "search_emails":
                    q = args.get("query", "is:unread")
                    emails = gmail_mgr.search_emails(q)
                    retrieved_emails.extend(emails)
                    step["status"] = "completed"
                    step["result"] = f"Found {len(emails)} emails"
                    for em in emails:
                        citations.append({
                            "source_type": "gmail",
                            "id": em.get("id", ""),
                            "title": em.get("subject", "Email"),
                            "timestamp": em.get("date", ""),
                            "snippet": em.get("snippet", ""),
                            "url": None
                        })
                elif action in ["draft_reply", "draft_email"]:
                    pending_action = {
                        "type": "send_email",
                        "to": args.get("to"),
                        "subject": args.get("subject"),
                        "body": args.get("body")
                    }
                    step["status"] = "completed"

            elif tool_name == "calendar":
                if action in ["list_upcoming_events", "check_calendar"]:
                    days = args.get("days_ahead", 7)
                    query = args.get("query")
                    events = calendar_mgr.list_upcoming_events(days_ahead=days, query=query)
                    retrieved_events.extend(events)
                    step["status"] = "completed"
                    step["result"] = f"Found {len(events)} events"
                    for ev in events:
                        citations.append({
                            "source_type": "calendar",
                            "id": ev.get("id", ""),
                            "title": ev.get("summary", "Event"),
                            "timestamp": ev.get("start", ""),
                            "snippet": ev.get("description", ""),
                            "url": ev.get("hangout_link")
                        })

            elif tool_name == "rag":
                rag_results = [{"snippet": "Interview preparation guidelines..."}]
                retrieved_emails.extend(rag_results)
                step["status"] = "completed"

            elif tool_name == "memory":
                step["status"] = "completed"

        return {
            "plan": plan,
            "retrieved_emails": retrieved_emails,
            "retrieved_events": retrieved_events,
            "retrieved_memories": retrieved_memories,
            "citations": citations,
            "pending_action": pending_action
        }

    builder.add_node("tool_executor", tool_executor)

    # 3. Synthesizer & Reasoning Node
    def synthesizer_node(state: MailMindState) -> Dict[str, Any]:
        prefs = state.get("user_preferences", {})
        prompt = SYNTHESIZER_PROMPT.format(
            emails=state.get("retrieved_emails", []),
            events=state.get("retrieved_events", []),
            memories=state.get("retrieved_memories", []),
            tone=prefs.get("tone", "Professional"),
            max_length=prefs.get("max_sentences", "Concise")
        )
        response = llm.invoke([
            SystemMessage(content=prompt),
            *state["messages"]
        ])
        return {
            "messages": [response],
            "final_response": response.content
        }

    builder.add_node("synthesizer", synthesizer_node)

    # 4. Human-in-the-Loop Interrupt Gate
    def hitl_gate(state: MailMindState) -> Command[Literal["executor_approved", "__end__"]]:
        action = state.get("pending_action")
        if not action:
            return Command(goto=END)

        # Interrupt execution and yield approval card to client
        approval_decision = interrupt({
            "action_type": action.get("type"),
            "target": action.get("to"),
            "subject": action.get("subject"),
            "body": action.get("body"),
            "prompt": "Please review this drafted action before MailMind dispatches it."
        })

        if approval_decision.get("approved"):
            return Command(
                goto="executor_approved",
                update={"action_approved": True, "user_feedback": approval_decision.get("feedback")}
            )
        else:
            return Command(
                goto=END,
                update={"action_approved": False, "user_feedback": "Action rejected by user."}
            )

    builder.add_node("hitl_gate", hitl_gate)

    # 5. Execution After Approval Node
    def executor_approved(state: MailMindState) -> Dict[str, Any]:
        action = state.get("pending_action", {})
        if action.get("type") == "send_email":
            gmail_mgr.send_email(
                to=action.get("to"),
                subject=action.get("subject"),
                body=action.get("body")
            )
        return {
            "messages": [AIMessage(content=f"✅ Approved action executed: Email dispatched to {action.get('to')}.")]
        }

    builder.add_node("executor_approved", executor_approved)

    # Graph Edges
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "tool_executor")
    builder.add_edge("tool_executor", "synthesizer")
    builder.add_edge("synthesizer", "hitl_gate")
    builder.add_edge("executor_approved", END)

    return builder.compile()
