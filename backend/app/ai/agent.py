"""The conversational agent loop — SPEC §2.1. Each Telegram turn calls this
once; it runs the tool-use loop server-side until Claude returns a plain
text reply (or a destructive tool needs user confirmation) and persists
the exchange to conversation history.
"""
import json
import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.ai.agent_tools import CONFIRMATION_REQUIRED, ToolError, dispatch_tool
from app.ai.client import create_message
from app.ai.context import format_mission, format_roles
from app.ai.tools.agent_tools_schema import AGENT_TOOLS
from app.config import settings
from app.services import conversation as conversation_service
from app.services import mission as mission_service
from app.services import roles as roles_service
from app.services import week_plans as week_plans_service
from app.services.iso_week import current_iso_week_plus
from app.services.summarize import summarize_messages

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 6

PERSONA = """You are Compass, a conversational planning assistant grounded in \
Stephen Covey's 7 Habits methodology, talking with your one user over Telegram.

- Use the tools given to read and write their planner. Never claim to have \
done something you didn't actually call a tool for.
- Look up ids with search_tasks/list_tasks before calling update_task/\
complete_task/drop_task if you don't already have the task's id from earlier \
in this conversation. Same for projects: call list_projects before \
breakdown_project/update_project/abandon_project if you don't already have \
the project's id — never guess or assume a project doesn't exist without \
checking list_projects first.
- Bias advice toward Q2 work (not urgent but important — planning, \
prevention, relationships, growth) and toward keeping big rocks scheduled \
first.
- Ask a clarifying question rather than guessing when the request is \
ambiguous (which role, which week, which of several matching tasks).
- Keep replies short and plain — this is a mobile chat, not a document. No \
heavy markdown tables."""


@dataclass
class AgentTurnResult:
    reply_text: str
    pending_confirmation: dict[str, Any] | None = None


def _build_system_prompt(db: Session) -> str:
    mission = mission_service.get_mission(db)
    roles = roles_service.list_roles(db, active_only=True)
    iso_week = current_iso_week_plus(0)
    plan = week_plans_service.get_week_plan_view(db, iso_week)
    big_rock_titles = ", ".join(t.title for t in plan["big_rocks"]) or "none pinned yet"

    return f"""{PERSONA}

Today's date: {date.today().isoformat()} (current ISO week: {iso_week})

Mission statement: {format_mission(mission)}

Roles:
{format_roles(roles)}

This week's ({iso_week}) big rocks: {big_rock_titles}"""


def _extract_text(content: list) -> str:
    texts = [b.text for b in content if b.type == "text"]
    return "\n".join(texts).strip()


def _maybe_summarize(db: Session) -> None:
    to_fold = conversation_service.messages_needing_summarization(db)
    if not to_fold:
        return
    existing = conversation_service.get_summary(db)
    new_summary = summarize_messages(existing.summary, to_fold)
    if new_summary is not None:
        conversation_service.apply_summarization(db, new_summary, to_fold)


def run_agent_turn(db: Session, user_text: str) -> AgentTurnResult:
    conversation_service.append_message(db, "user", user_text)

    system = _build_system_prompt(db)
    summary = conversation_service.get_summary(db)
    history = conversation_service.get_recent_messages(db)

    messages: list[dict[str, Any]] = []
    if summary.summary:
        messages.append(
            {"role": "user", "content": f"[Earlier conversation summary: {summary.summary}]"}
        )
        messages.append({"role": "assistant", "content": "Understood, I have that context."})
    for m in history:
        messages.append({"role": m.role, "content": m.content})

    final_text: str | None = None
    pending_confirmation: dict[str, Any] | None = None

    for _ in range(MAX_TOOL_ITERATIONS):
        response = create_message(
            system=system, messages=messages, tools=AGENT_TOOLS, model=settings.anthropic_model
        )
        if response is None:
            final_text = "I'm having trouble reaching the AI right now. Try again in a bit."
            break

        messages.append(
            {"role": "assistant", "content": [b.model_dump() for b in response.content]}
        )

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            final_text = _extract_text(response.content)
            break

        tool_results = []
        for block in tool_use_blocks:
            if block.name in CONFIRMATION_REQUIRED:
                pending_confirmation = {"tool_name": block.name, "args": block.input}
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": (
                            "Waiting for the user to confirm or cancel this action via the "
                            "inline keyboard that was just sent. Wrap up your reply now."
                        ),
                    }
                )
                continue
            try:
                result = dispatch_tool(db, block.name, block.input)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)}
                )
            except ToolError as e:
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Error: {e}",
                        "is_error": True,
                    }
                )

        messages.append({"role": "user", "content": tool_results})

    if final_text is None:
        final_text = "That's taking more steps than I can do in one go — could you split it up?"

    conversation_service.append_message(db, "assistant", final_text)
    _maybe_summarize(db)

    return AgentTurnResult(reply_text=final_text, pending_confirmation=pending_confirmation)
