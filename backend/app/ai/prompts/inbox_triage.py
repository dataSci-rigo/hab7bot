from app.ai.context import format_projects, format_roles
from app.models.project import Project
from app.models.role import Role
from app.models.task import Task

SYSTEM = """You are Compass's inbox triage assistant. You'll be given every \
task currently sitting untriaged in the inbox, plus the roles and projects \
that exist. For EACH task (echo back its task_id exactly), infer:

- role_name: the single best-matching role by exact name, or omit (null) if \
nothing matches well.
- quadrant: Q1 (urgent+important), Q2 (not urgent+important — the default \
for most planning/growth work), Q3 (urgent+not important), or Q4 (neither).
- is_big_rock_candidate: true only if this looks like a significant, \
important piece of work worth protecting time for.
- project_title_match: if the task clearly belongs to one of the existing \
projects listed, that project's exact title. Otherwise omit (null).

Return one item per task_id given, in any order, but never drop a task."""


def build_user_message(tasks: list[Task], roles: list[Role], projects: list[Project]) -> str:
    roles_by_id = {r.id: r.name for r in roles}
    task_lines = "\n".join(f"- task_id={t.id} : \"{t.title}\"" for t in tasks)
    return f"""Roles:
{format_roles(roles)}

Existing projects:
{format_projects(projects, roles_by_id)}

Inbox tasks to triage:
{task_lines}

Infer metadata for every task listed above."""
