import logging
from typing import Any

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def call_tool(
    *,
    system: str,
    user_message: str,
    tool_name: str,
    tool_description: str,
    input_schema: dict[str, Any],
    model: str,
    max_retries: int = 1,
    timeout: float = 30.0,
) -> dict[str, Any] | None:
    """Force a single forced tool call and return its parsed input.

    Returns None on any failure (missing key, timeout, API error) so callers
    can degrade gracefully instead of raising — per CLAUDE.md ground rule 6.
    """
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY not set; skipping AI call for tool %s", tool_name)
        return None

    client = _get_client()
    attempts = max_retries + 1
    for attempt in range(1, attempts + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": user_message}],
                tools=[
                    {
                        "name": tool_name,
                        "description": tool_description,
                        "input_schema": input_schema,
                    }
                ],
                tool_choice={"type": "tool", "name": tool_name},
                timeout=timeout,
            )
        except Exception:
            logger.warning(
                "AI call failed (attempt %d/%d) for tool %s", attempt, attempts, tool_name,
                exc_info=True,
            )
            continue

        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                return block.input
        logger.warning("AI response for tool %s had no matching tool_use block", tool_name)
        return None

    return None
