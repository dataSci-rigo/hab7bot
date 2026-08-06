from app.ai.context import format_existing_tasks, format_mission
from app.models.goal import Goal
from app.models.mission import MissionStatement
from app.models.project import Project
from app.models.role import Role
from app.models.task import Task

SYSTEM = """You are Compass, a planning assistant grounded in Stephen Covey's \
7 Habits methodology. Break the given project into milestones and concrete tasks.

Rules:
- Each task must have a title, an estimate in minutes, a quadrant (Q1-Q4; \
default Q2 — not urgent but important — unless the task is clearly urgent \
firefighting), and a suggested_week_offset (0 = this week, 1 = next week, etc).
- Bias toward Q2 work: planning, prevention, relationship-building, growth.
- If you are missing information needed to break this down well, list \
clarifying questions instead of guessing wildly.
- List any assumptions you made.
- Keep milestones and tasks concrete and actionable, not vague."""


def build_user_message(
    project: Project,
    role: Role,
    goal: Goal | None,
    mission: MissionStatement,
    existing_tasks: list[Task],
) -> str:
    goal_line = f"Serves goal: {goal.title}" if goal else "Not tied to a specific goal."
    return f"""Mission statement: {format_mission(mission)}

Role: {role.name}
{goal_line}

Project: {project.title}
Notes: {project.notes or "(none)"}

Existing tasks already in this project:
{format_existing_tasks(existing_tasks)}

Break this project down into milestones and tasks."""
