"""Seed script — creates demo roles/goals/tasks for local development.

Run: python -m app.seed
"""
from app.db import SessionLocal
from app.models.enums import Quadrant, TaskStatus
from app.schemas.goal import GoalCreate
from app.schemas.role import RoleCreate
from app.schemas.task import TaskCreate
from app.services import goals as goals_service
from app.services import roles as roles_service
from app.services import tasks as tasks_service


def seed() -> None:
    db = SessionLocal()
    try:
        engineer = roles_service.create_role(
            db, RoleCreate(name="Engineer", description="Career & craft")
        )
        health = roles_service.create_role(
            db, RoleCreate(name="Health & Fitness", description="Body and energy")
        )

        goals_service.create_goal(
            db, GoalCreate(role_id=engineer.id, title="Ship Compass v1")
        )
        goals_service.create_goal(
            db, GoalCreate(role_id=health.id, title="Run a half marathon")
        )

        tasks_service.create_task(
            db,
            TaskCreate(
                title="Write Phase 1 domain models",
                role_id=engineer.id,
                quadrant=Quadrant.Q2,
                is_big_rock=True,
                status=TaskStatus.done,
            ),
        )
        tasks_service.create_task(
            db,
            TaskCreate(
                title="Go for a 5k run",
                role_id=health.id,
                quadrant=Quadrant.Q2,
            ),
        )
        print("Seeded 2 roles, 2 goals, 2 tasks.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
