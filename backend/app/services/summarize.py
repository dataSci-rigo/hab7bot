import logging

from app.ai.client import call_tool
from app.config import settings
from app.models.conversation import ConversationMessage

logger = logging.getLogger(__name__)

_SYSTEM = """Summarize this planning-chat conversation excerpt into a short \
paragraph capturing decisions made, open questions, and anything the \
assistant should still remember. Fold it in with the existing summary \
given, don't just append — keep the whole thing under ~150 words."""

_TOOL = {
    "name": "record_summary",
    "description": "Record the updated rolling conversation summary.",
    "input_schema": {
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
    },
}


def summarize_messages(existing_summary: str, messages: list[ConversationMessage]) -> str | None:
    """Returns None on AI failure — caller should just skip summarizing this
    round rather than losing history (messages aren't deleted until this
    succeeds)."""
    transcript = "\n".join(f"{m.role}: {m.content}" for m in messages)
    user_message = (
        f"Existing summary: {existing_summary or '(none yet)'}\n\nNew messages:\n{transcript}"
    )

    raw = call_tool(
        system=_SYSTEM,
        user_message=user_message,
        tool_name=_TOOL["name"],
        tool_description=_TOOL["description"],
        input_schema=_TOOL["input_schema"],
        model=settings.anthropic_model_fast,
        timeout=20.0,
    )
    if raw is None:
        return None
    return raw.get("summary")
