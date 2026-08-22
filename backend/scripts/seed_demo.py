"""Build the guest showcase database (compass_demo.db) from scratch.

Read-only guest sessions (GUEST_PASSWORD login) are served from this separate
DB so guests browse a rich, curated demo instead of the owner's real planner.
Rerunnable: wipes the demo DB and reseeds. Dates are computed relative to the
current ISO week so the demo always shows a lively "this week".

Run:  python -m scripts.seed_demo
"""
import os
from datetime import date, datetime, time, timedelta
from pathlib import Path

from alembic.config import Config

from alembic import command
from app.ai.schemas import WeekAnalysis
from app.config import BACKEND_DIR, settings


def _wipe_demo_db() -> None:
    demo_path = Path(settings.demo_database_url.removeprefix("sqlite:///"))
    assert "demo" in demo_path.name, f"refusing to wipe non-demo DB: {demo_path}"
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(demo_path) + suffix)
        if p.exists():
            p.unlink()


def _migrate_demo_db() -> None:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    os.environ["ALEMBIC_DATABASE_URL"] = settings.demo_database_url
    try:
        command.upgrade(cfg, "head")
    finally:
        del os.environ["ALEMBIC_DATABASE_URL"]


def _monday(iso_week_offset: int) -> date:
    today = date.today()
    monday = today - timedelta(days=today.isoweekday() - 1)
    return monday + timedelta(weeks=iso_week_offset)


def _iso(week_offset: int) -> str:
    from app.services.iso_week import iso_week_string

    return iso_week_string(_monday(week_offset))


def seed() -> None:
    # Imported after migration so the module-level demo engine binds cleanly.
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.models import (
        Goal,
        MissionStatement,
        Project,
        Role,
        RoleWeekIntention,
        Task,
        WeeklyReview,
        WeekPlan,
    )
    from app.models.enums import ProjectStatus, Quadrant, TaskStatus
    from app.services.weekly_review import compute_week_stats

    engine = create_engine(
        settings.demo_database_url, connect_args={"check_same_thread": False}
    )
    db = sessionmaker(bind=engine)()

    db.add(
        MissionStatement(
            content=(
                "Live deliberately: put the big rocks in first. Build things that "
                "matter, stay strong enough to enjoy them, and be fully present "
                "for the people I love."
            )
        )
    )

    engineer = Role(name="Engineer", description="Ship meaningful software, keep learning")
    parent = Role(name="Parent", description="Present, patient, playful")
    health = Role(name="Health", description="Strength, sleep, endurance")
    writer = Role(name="Writer", description="Think in public, one essay a month")
    db.add_all([engineer, parent, health, writer])
    db.flush()

    goals = [
        Goal(role_id=engineer.id, title="Launch the side project publicly",
             target_date=_monday(6), notes="Real users by end of quarter"),
        Goal(role_id=parent.id, title="Weekly one-on-one adventure with each kid",
             notes="Small, consistent, screen-free"),
        Goal(role_id=health.id, title="Run a sub-2:00 half marathon", target_date=_monday(10)),
        Goal(role_id=writer.id, title="Publish 6 essays this year"),
    ]
    db.add_all(goals)
    db.flush()

    launch = Project(role_id=engineer.id, goal_id=goals[0].id, title="Public launch of Compass",
                     status=ProjectStatus.active, notes="Landing page, docs, demo video")
    marathon = Project(role_id=health.id, goal_id=goals[2].id, title="Half-marathon training block",
                       status=ProjectStatus.active)
    essays = Project(role_id=writer.id, goal_id=goals[3].id, title="Essay: what planners get wrong",
                     status=ProjectStatus.active)
    treehouse = Project(role_id=parent.id, title="Backyard treehouse", status=ProjectStatus.idea,
                        notes="Summer build with the kids")
    db.add_all([launch, marathon, essays, treehouse])
    db.flush()

    def task(title, role, *, project=None, quadrant=Quadrant.Q2, week=0, day=None,
             status=TaskStatus.planned, big_rock=False, estimate=None, actual=None,
             done_on=None, created_days_before=3) -> Task:
        scheduled_week = _iso(week) if week is not None else None
        scheduled_day = _monday(week) + timedelta(days=day) if day is not None else None
        completed_at = None
        if status == TaskStatus.done:
            done_day = done_on if done_on is not None else (scheduled_day or _monday(week))
            completed_at = datetime.combine(done_day, time(17, 30))
        t = Task(
            title=title, role_id=role.id, project_id=project.id if project else None,
            quadrant=quadrant, is_big_rock=big_rock, status=status,
            scheduled_week=scheduled_week, scheduled_day=scheduled_day,
            estimate_minutes=estimate, actual_minutes=actual, completed_at=completed_at,
        )
        if completed_at is not None:
            t.created_at = completed_at - timedelta(days=created_days_before)
        return t

    # ── two finished weeks of history (rich stats + reviews) ────────────────
    for offset, done_rate in ((-2, 5), (-1, 6)):
        history = [
            task("Ship onboarding flow", engineer, project=launch, big_rock=True,
                 status=TaskStatus.done, week=offset, day=1, estimate=120, actual=150),
            task("Long run (14 km)", health, project=marathon, big_rock=True,
                 status=TaskStatus.done, week=offset, day=5, estimate=90, actual=85),
            task("Essay outline and first draft", writer, project=essays, big_rock=True,
                 status=TaskStatus.done if offset == -1 else TaskStatus.planned,
                 week=offset, day=3, estimate=90, actual=110),
            task("Museum morning with the kids", parent, quadrant=Quadrant.Q2,
                 status=TaskStatus.done, week=offset, day=5, estimate=180, actual=180),
            task("Fix flaky deploy pipeline", engineer, quadrant=Quadrant.Q1,
                 status=TaskStatus.done, week=offset, day=0, estimate=60, actual=45),
            task("Interval session", health, project=marathon,
                 status=TaskStatus.done, week=offset, day=2, estimate=45, actual=45),
            task("Expense report", engineer, quadrant=Quadrant.Q3,
                 status=TaskStatus.done if done_rate > 5 else TaskStatus.planned,
                 week=offset, day=4, estimate=30, actual=25),
        ]
        db.add_all(history)
    db.flush()

    for offset, reflection, summary, trend in (
        (-2,
         "Solid restart week. The morning brief kept me honest.",
         "A strong restart: 2 of 3 big rocks landed and Q2 effort led the week at "
         "roughly 60% of logged minutes. The essay slipped — it never got a "
         "protected block.",
         "no prior data yet"),
        (-1,
         "Best week in months. Scheduling the essay before email was the unlock.",
         "All 3 big rocks completed — first clean sweep. Q2 share climbed again and "
         "the one Q3 item (expense report) was batched into a Friday slot instead of "
         "fragmenting the week.",
         "climbing for the second week"),
    ):
        analysis = WeekAnalysis(
            summary=summary,
            wins=["Big rocks scheduled before anything else",
                  "Training plan fully intact", "Screen-free family block protected"],
            concerns=["Writer role starves when the week gets busy"],
            patterns=["Deep work lands when scheduled before 10am"],
            suggestions=[{
                "change": "Give the essay a recurring Tuesday 8-10am block",
                "why": "It slipped whenever it lacked a protected slot",
                "how": "Schedule it as a big rock before planning anything else",
            }],
            suggested_big_rock_candidates_next_week=[
                "Compass launch checklist", "16 km long run", "Essay final edit"],
            q2_percent_trend=trend,
        )
        db.add(WeeklyReview(
            iso_week=_iso(offset),
            stats=compute_week_stats(db, _iso(offset)),
            ai_analysis=analysis.model_dump(),
            reflection=reflection,
        ))

    # ── the current, in-flight week ─────────────────────────────────────────
    current = [
        task("Record the Compass demo video", engineer, project=launch, big_rock=True,
             week=0, day=1, estimate=120, status=TaskStatus.done),
        task("16 km long run", health, project=marathon, big_rock=True,
             week=0, day=5, estimate=100),
        task("Essay final edit + publish", writer, project=essays, big_rock=True,
             week=0, day=2, estimate=90, status=TaskStatus.in_progress),
        task("Plan weekend bike trip", parent, week=0, day=3, estimate=30),
        task("Review landing page copy", engineer, project=launch, week=0, day=2,
             estimate=45, status=TaskStatus.done),
        task("Tempo run", health, project=marathon, week=0, day=1,
             estimate=45, status=TaskStatus.done),
        task("Renew passports", parent, quadrant=Quadrant.Q1, week=0, day=4, estimate=40),
        task("Answer conference CFP", writer, quadrant=Quadrant.Q3, week=0, day=4, estimate=30),
    ]
    db.add_all(current)

    # inbox: captured, not yet triaged — shows the triage flow
    db.add_all([
        Task(title="Look into standing desk options", role_id=engineer.id,
             status=TaskStatus.inbox),
        Task(title="Sign kids up for swim lessons", role_id=parent.id,
             status=TaskStatus.inbox, quadrant=Quadrant.Q1),
        Task(title="Idea: essay on calendar bankruptcy", role_id=writer.id,
             status=TaskStatus.inbox),
    ])

    plan = WeekPlan(iso_week=_iso(0))
    db.add(plan)
    db.flush()
    db.add_all([
        RoleWeekIntention(week_plan_id=plan.id, role_id=engineer.id,
                          note="Launch week — demo video is the one thing"),
        RoleWeekIntention(week_plan_id=plan.id, role_id=health.id,
                          note="Peak week of the training block"),
        RoleWeekIntention(week_plan_id=plan.id, role_id=parent.id,
                          note="Say yes to every game of catch"),
    ])

    db.commit()
    db.close()
    print(f"Seeded demo DB → {settings.demo_database_url}")
    print(f"  weeks: {_iso(-2)}, {_iso(-1)}, {_iso(0)} (current)")


def main() -> None:
    _wipe_demo_db()
    _migrate_demo_db()
    seed()


if __name__ == "__main__":
    main()
