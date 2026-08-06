from pydantic import BaseModel, Field

from app.models.enums import Quadrant

# ── §3.1 project breakdown ──────────────────────────────────────────────────


class BreakdownTask(BaseModel):
    title: str
    estimate_minutes: int | None = None
    quadrant: Quadrant = Quadrant.Q2
    suggested_week_offset: int = Field(default=0, description="0 = this week, 1 = next week, etc.")


class BreakdownMilestone(BaseModel):
    title: str
    tasks: list[BreakdownTask]


class BreakdownProposal(BaseModel):
    milestones: list[BreakdownMilestone]
    assumptions: list[str] = []
    questions: list[str] = []


# ── §3.2 project suggestions ─────────────────────────────────────────────────


class ProjectSuggestion(BaseModel):
    title: str
    role_name: str
    goal_title: str | None = None
    rationale: str
    first_three_tasks: list[str]
    quadrant_profile: str


class ProjectSuggestionsOutput(BaseModel):
    suggestions: list[ProjectSuggestion]


# ── §3.4 capture-time inference ──────────────────────────────────────────────


class CaptureInference(BaseModel):
    title: str
    role_name: str | None = None
    quadrant: Quadrant = Quadrant.Q2
    is_big_rock_candidate: bool = False
    project_title_match: str | None = None


# ── Inbox "AI triage" (SPEC §2.2.2 — batches capture-inference over the inbox) ──


class InboxTriageItem(BaseModel):
    task_id: str
    role_name: str | None = None
    quadrant: Quadrant = Quadrant.Q2
    is_big_rock_candidate: bool = False
    project_title_match: str | None = None


class InboxTriageOutput(BaseModel):
    items: list[InboxTriageItem]
