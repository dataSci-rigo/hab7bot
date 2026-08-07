from app.models.role import Role
from app.models.task import Task


def capture_confirmation_text(task: Task, role: Role | None) -> str:
    role_label = role.name if role else "no role"
    rock = " ⭐" if task.is_big_rock else ""
    return f"Saved: {task.title}\n{role_label} · {task.quadrant.value}{rock}"
