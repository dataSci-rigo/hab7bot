from app.ai.context import format_projects, format_roles
from app.models.project import Project
from app.models.role import Role

SYSTEM = """You are Compass's fast capture assistant. Given a short piece of \
captured text, infer how it should be filed as a task.

Rules:
- title: a clean, short task title (clean up the raw capture text if needed).
- role_name: the single best-matching role from the list given, by exact \
name. Omit (null) if nothing matches well.
- quadrant: Q1 (urgent+important), Q2 (not urgent+important — the default \
for most planning/growth work), Q3 (urgent+not important), or Q4 (neither).
- is_big_rock_candidate: true only if this looks like a significant, \
important piece of work worth protecting time for — not a small errand.
- project_title_match: if this task clearly belongs to one of the existing \
projects listed, give that project's exact title. Otherwise omit (null)."""


def build_user_message(text: str, roles: list[Role], projects: list[Project]) -> str:
    roles_by_id = {r.id: r.name for r in roles}
    return f"""Roles:
{format_roles(roles)}

Existing projects:
{format_projects(projects, roles_by_id)}

Captured text: "{text}"

Infer this task's metadata."""
