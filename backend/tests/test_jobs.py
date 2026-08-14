from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.orm import Session

from app.bot.jobs import run_tick
from app.schemas.role import RoleCreate
from app.schemas.task import TaskCreate
from app.services import conversation as conversation_service
from app.services import roles as roles_service
from app.services import tasks as tasks_service
from app.services import week_plans as week_plans_service
from app.services import weekly_review as weekly_review_service

MONDAY = datetime(2026, 8, 17, 7, 31)  # after default morning_brief_time 07:30
SUNDAY = datetime(2026, 8, 16, 16, 1)  # after default weekly_review_time 16:00


class FakeBot:
    def __init__(self) -> None:
        self.send_message = AsyncMock()


class FakeContext:
    def __init__(self) -> None:
        self.bot = FakeBot()


@pytest.mark.asyncio
async def test_morning_brief_fires_once_per_day(db_session: Session) -> None:
    context = FakeContext()

    await run_tick(db_session, context, MONDAY)
    await run_tick(db_session, context, MONDAY)

    assert context.bot.send_message.await_count == 1
    text = context.bot.send_message.await_args.kwargs["text"]
    assert "Good morning" in text


@pytest.mark.asyncio
async def test_morning_brief_persisted_as_assistant_turn(db_session: Session) -> None:
    context = FakeContext()

    await run_tick(db_session, context, MONDAY)

    history = conversation_service.get_recent_messages(db_session)
    assert len(history) == 1
    assert history[0].role == "assistant"
    assert "Good morning" in history[0].content


@pytest.mark.asyncio
async def test_morning_brief_lists_todays_scheduled_tasks(db_session: Session) -> None:
    role = roles_service.create_role(db_session, RoleCreate(name="Engineer"))
    tasks_service.create_task(
        db_session,
        TaskCreate(title="Ship the report", role_id=role.id, scheduled_day=MONDAY.date()),
    )
    context = FakeContext()

    await run_tick(db_session, context, MONDAY)

    text = context.bot.send_message.await_args.kwargs["text"]
    assert "Ship the report" in text


@pytest.mark.asyncio
async def test_evening_checkin_does_not_fire_before_configured_time(db_session: Session) -> None:
    context = FakeContext()

    await run_tick(db_session, context, MONDAY)  # 07:31 — before 21:00 default

    assert context.bot.send_message.await_count == 1  # morning brief only


@pytest.mark.asyncio
async def test_evening_checkin_fires_once(db_session: Session) -> None:
    evening = datetime(2026, 8, 17, 21, 5)
    context = FakeContext()

    await run_tick(db_session, context, evening)
    await run_tick(db_session, context, evening)

    # morning brief (past its time too) + evening check-in = 2 sends, not 4
    assert context.bot.send_message.await_count == 2


@pytest.mark.asyncio
async def test_weekly_review_generated_once_on_sunday(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []
    monkeypatch.setattr(
        "app.services.weekly_review.analyze_week",
        lambda stats, previous, reflection: calls.append(1) or None,
    )
    context = FakeContext()

    await run_tick(db_session, context, SUNDAY)
    await run_tick(db_session, context, SUNDAY)

    assert len(calls) == 1
    assert weekly_review_service.get_review(db_session, "2026-W33") is not None


@pytest.mark.asyncio
async def test_weekly_review_not_generated_before_configured_time(db_session: Session) -> None:
    early_sunday = datetime(2026, 8, 16, 10, 0)  # before default 16:00
    context = FakeContext()

    await run_tick(db_session, context, early_sunday)

    assert weekly_review_service.get_review(db_session, "2026-W33") is None


@pytest.mark.asyncio
async def test_planning_prompt_fires_once_and_marks_week_plan(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 17:01 is also past the default 16:00 weekly_review_time, so the tick
    # generates a review too — stub analyze_week so this doesn't hit the
    # real Anthropic API (ground rule 9).
    monkeypatch.setattr(
        "app.services.weekly_review.analyze_week", lambda stats, previous, reflection: None
    )
    planning_time = datetime(2026, 8, 16, 17, 1)  # after default 17:00
    context = FakeContext()

    await run_tick(db_session, context, planning_time)
    await run_tick(db_session, context, planning_time)

    week_plan = week_plans_service.get_or_create_week_plan(db_session, "2026-W33")
    assert week_plan.planning_prompt_sent_at is not None
    # morning brief + weekly planning = 2 sends (17:01 is before the default
    # 21:00 evening check-in time, so that one doesn't fire here)
    assert context.bot.send_message.await_count == 2


@pytest.mark.asyncio
async def test_planning_prompt_does_not_fire_on_a_weekday(db_session: Session) -> None:
    context = FakeContext()

    await run_tick(db_session, context, datetime(2026, 8, 17, 17, 1))  # Monday

    week_plan = week_plans_service.get_or_create_week_plan(db_session, "2026-W34")
    assert week_plan.planning_prompt_sent_at is None


@pytest.mark.asyncio
async def test_force_tick_fires_all_four_behaviors_on_a_weekday(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.services.weekly_review.analyze_week", lambda stats, previous, reflection: None
    )
    context = FakeContext()

    await run_tick(db_session, context, datetime(2026, 8, 17, 9, 0), force=True)  # Monday 09:00

    # morning brief + evening check-in + weekly planning = 3 sends (weekly
    # review generation doesn't send a message of its own)
    assert context.bot.send_message.await_count == 3
    assert weekly_review_service.get_review(db_session, "2026-W34") is not None
    week_plan = week_plans_service.get_or_create_week_plan(db_session, "2026-W34")
    assert week_plan.planning_prompt_sent_at is not None


@pytest.mark.asyncio
async def test_force_tick_fires_again_even_if_already_sent_today(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.services.weekly_review.analyze_week", lambda stats, previous, reflection: None
    )
    context = FakeContext()
    moment = datetime(2026, 8, 17, 9, 0)

    await run_tick(db_session, context, moment, force=True)
    await run_tick(db_session, context, moment, force=True)

    assert context.bot.send_message.await_count == 6
