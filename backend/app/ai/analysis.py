import logging

from pydantic import ValidationError

from app.ai.client import call_tool
from app.ai.prompts import analysis as analysis_prompt
from app.ai.schemas import WeekAnalysis
from app.ai.tools.definitions import WEEK_ANALYSIS_TOOL
from app.config import settings

logger = logging.getLogger(__name__)


def analyze_week(
    stats: dict, previous_analyses: list[dict], reflection: str | None
) -> WeekAnalysis | None:
    """§3.3 — pure function, no DB access: the caller (weekly_review service)
    gathers stats/previous reviews so this module stays a thin AI-call
    wrapper, matching the rest of app/ai/'s single-shot features.
    """
    raw = call_tool(
        system=analysis_prompt.SYSTEM,
        user_message=analysis_prompt.build_user_message(stats, previous_analyses, reflection),
        tool_name=WEEK_ANALYSIS_TOOL["name"],
        tool_description=WEEK_ANALYSIS_TOOL["description"],
        input_schema=WEEK_ANALYSIS_TOOL["input_schema"],
        model=settings.anthropic_model,
        timeout=90.0,
    )
    if raw is None:
        return None
    try:
        return WeekAnalysis.model_validate(raw)
    except ValidationError:
        logger.warning("Week analysis response failed schema validation", exc_info=True)
        return None
