"""Anthropic tool-use definitions — one per AI feature. `input_schema` is the
JSON Schema Claude is forced to fill in (via tool_choice); it's derived
directly from the Pydantic response models in app/ai/schemas.py so the two
never drift apart.
"""
from app.ai.schemas import (
    BreakdownProposal,
    CaptureInference,
    InboxTriageOutput,
    ProjectSuggestionsOutput,
)

BREAKDOWN_TOOL = {
    "name": "propose_breakdown",
    "description": "Propose a milestone/task breakdown for a project.",
    "input_schema": BreakdownProposal.model_json_schema(),
}

SUGGESTIONS_TOOL = {
    "name": "propose_project_suggestions",
    "description": "Propose up to 5 new projects grounded in mission/roles/goals.",
    "input_schema": ProjectSuggestionsOutput.model_json_schema(),
}

CAPTURE_TOOL = {
    "name": "infer_task_metadata",
    "description": "Infer role, quadrant, and other metadata for a captured task.",
    "input_schema": CaptureInference.model_json_schema(),
}

INBOX_TRIAGE_TOOL = {
    "name": "triage_inbox",
    "description": "Infer metadata for every task currently in the inbox.",
    "input_schema": InboxTriageOutput.model_json_schema(),
}
