"""Match AI-returned names back to real DB rows.

The model is asked to echo back a role/project by exact name rather than by
id (it can't know our UUIDs), so callers resolve those names here — case-
insensitively, exact match only. No fuzzy matching: an unmatched name just
means the field is left unset and the surface falls back to its own default.
"""
from app.models.project import Project
from app.models.role import Role


def resolve_role(role_name: str | None, roles: list[Role]) -> Role | None:
    if not role_name:
        return None
    needle = role_name.strip().lower()
    for role in roles:
        if role.name.strip().lower() == needle:
            return role
    return None


def resolve_project(project_title: str | None, projects: list[Project]) -> Project | None:
    if not project_title:
        return None
    needle = project_title.strip().lower()
    for project in projects:
        if project.title.strip().lower() == needle:
            return project
    return None
