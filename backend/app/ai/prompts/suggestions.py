from app.ai.context import format_goals, format_mission, format_projects, format_roles
from app.models.goal import Goal
from app.models.mission import MissionStatement
from app.models.project import Project
from app.models.role import Role

SYSTEM = """You are Compass, a planning assistant grounded in Stephen Covey's \
7 Habits methodology. Suggest new projects grounded in the user's mission, \
roles, and goals.

Rules:
- Suggest at most 5 projects, ranked with the most valuable first.
- Bias toward: roles with little recent activity, goals with an approaching \
target date and no active project serving them, and absent Q2/"Sharpen the \
Saw" (renewal, growth, health, learning) work.
- Each suggestion needs a title, the role it belongs to (role_name, must \
exactly match one of the roles given), an optional goal_title if it serves \
one of the listed goals, a one- or two-sentence rationale, three concrete \
first tasks, and a short quadrant_profile describing the kind of work \
involved (e.g. "mostly Q2 planning and research").
- Do not suggest a project that duplicates an existing active/idea project."""


def build_user_message(
    mission: MissionStatement,
    roles: list[Role],
    goals: list[Goal],
    projects: list[Project],
) -> str:
    roles_by_id = {r.id: r.name for r in roles}
    return f"""Mission statement: {format_mission(mission)}

Roles:
{format_roles(roles)}

Goals:
{format_goals(goals, roles_by_id)}

Existing active/idea projects (avoid duplicating these):
{format_projects(projects, roles_by_id)}

Suggest up to 5 new projects."""
