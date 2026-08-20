"""Bot worker background jobs — registered on PTB's JobQueue (APScheduler-
backed). Phase 5 added google_sync_job; Phase 6 adds scheduler_tick_job onto
the same queue rather than introducing a second scheduler.
"""
import logging
from datetime import date, datetime

from sqlalchemy.orm import Session
from telegram.ext import ContextTypes

from app.config import settings
from app.db import SessionLocal
from app.integrations.google.sync import sync_all
from app.models.enums import TaskStatus
from app.services import conversation as conversation_service
from app.services import daily_log as daily_log_service
from app.services import settings as settings_service
from app.services import tasks as tasks_service
from app.services import week_plans as week_plans_service
from app.services import weekly_review as weekly_review_service
from app.services.clock import now
from app.services.iso_week import iso_week_string

logger = logging.getLogger(__name__)

GOOGLE_SYNC_INTERVAL_SECONDS = 600  # 10 minutes
SCHEDULER_TICK_INTERVAL_SECONDS = 60


async def google_sync_job(_context: ContextTypes.DEFAULT_TYPE) -> None:
    with SessionLocal() as db:
        if not settings_service.get_settings(db).google_sync_enabled:
            return
        result = sync_all(db)
    if not result["ok"]:
        logger.info("Scheduled Google sync skipped/failed: %s", result.get("reason"))


async def _push_proactive_message(
    context: ContextTypes.DEFAULT_TYPE, db: Session, text: str
) -> None:
    """Sends a bot-initiated message and records it as an assistant turn in
    conversation history, so the user's next free-text reply flows through
    the ordinary run_agent_turn path unchanged (SPEC §2.1 guided prompts).

    Send first, then record — if the Telegram call fails (transient network
    error), nothing is written to history, so the caller's "already sent"
    flag also stays unset and the next tick/retry sends a clean single copy
    instead of leaving an orphaned or duplicated history row.
    """
    await context.bot.send_message(chat_id=settings.telegram_allowed_user_id, text=text)
    conversation_service.append_message(db, "assistant", text)


async def _send_morning_brief(
    context: ContextTypes.DEFAULT_TYPE, db: Session, today_date: date
) -> None:
    iso_week = iso_week_string(today_date)
    plan = week_plans_service.get_week_plan_view(db, iso_week)
    todays_tasks = tasks_service.list_tasks(db, scheduled_day=today_date)

    task_lines = "\n".join(f"- {t.title}" for t in todays_tasks) or "Nothing scheduled for today."
    big_rock_titles = ", ".join(t.title for t in plan["big_rocks"]) or "none pinned yet"

    text = (
        f"Good morning! Today ({today_date.isoformat()}):\n{task_lines}\n\n"
        f"This week's big rocks: {big_rock_titles}"
    )
    await _push_proactive_message(context, db, text)


async def _send_evening_checkin_prompt(context: ContextTypes.DEFAULT_TYPE, db: Session) -> None:
    text = "Evening check-in — what got done today? Anything worth noting for tomorrow?"
    await _push_proactive_message(context, db, text)


async def _send_planning_prompt(
    context: ContextTypes.DEFAULT_TYPE, db: Session, iso_week: str
) -> None:
    review = weekly_review_service.get_review(db, iso_week)
    summary = (
        review.ai_analysis["summary"]
        if review and review.ai_analysis
        else "No analysis available yet."
    )
    inbox_count = len(tasks_service.list_tasks(db, status=TaskStatus.inbox))

    text = (
        f"Time to plan next week. Last week: {summary}\n\n"
        f"{inbox_count} task(s) still in your inbox to triage. Tell me your big rocks per "
        f"role, or say \"help me plan\" and I'll walk you through it.\n\n"
        f"Full picture: {settings.web_app_url}/review/{iso_week}"
    )
    await _push_proactive_message(context, db, text)


async def run_tick(
    db: Session, context: ContextTypes.DEFAULT_TYPE, current: datetime, force: bool = False
) -> None:
    """Core tick logic, taking `db`/`current` as plain arguments so it can be
    tested directly (simulated clock) without going through PTB's JobQueue —
    mirrors how test_google_sync.py tests sync_tasks(db_session) rather than
    the google_sync_job wrapper.

    `force=True` bypasses the day-of-week/time-of-day/already-sent gating and
    fires all four behaviors unconditionally — used by the bot's `/debug
    tick` command so weekly-only behaviors (review/planning, normally
    Sunday-gated) can be exercised without waiting for an actual Sunday.
    """
    app_settings = settings_service.get_settings(db)
    current_time_str = current.strftime("%H:%M")
    today_date = current.date()
    log = daily_log_service.get_or_create_log(db, today_date)

    send_morning = force or (
        not log.morning_brief_sent and current_time_str >= app_settings.morning_brief_time
    )
    if send_morning:
        await _send_morning_brief(context, db, today_date)
        daily_log_service.mark_morning_brief_sent(db, log)

    send_evening = force or (
        not log.evening_checkin_sent and current_time_str >= app_settings.evening_checkin_time
    )
    if send_evening:
        await _send_evening_checkin_prompt(context, db)
        daily_log_service.mark_evening_checkin_sent(db, log)

    if force or current.isoweekday() == 7:  # Sunday — SPEC's review/planning anchor day
        iso_week = iso_week_string(today_date)

        if force or current_time_str >= app_settings.weekly_review_time:
            weekly_review_service.generate_review(db, iso_week, force=force)

        week_plan = week_plans_service.get_or_create_week_plan(db, iso_week)
        send_planning = force or (
            week_plan.planning_prompt_sent_at is None
            and current_time_str >= app_settings.weekly_planning_time
        )
        if send_planning:
            await _send_planning_prompt(context, db, iso_week)
            week_plan.planning_prompt_sent_at = current
            db.commit()


async def scheduler_tick_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Polls every SCHEDULER_TICK_INTERVAL_SECONDS instead of registering
    fixed-at-startup run_daily jobs — AppSettings' check-in/brief/planning
    times are user-editable via the web Settings page, and re-reading them
    fresh each tick means an edit takes effect within a minute without a
    bot-worker restart or job-requeue logic.
    """
    with SessionLocal() as db:
        await run_tick(db, context, now())
