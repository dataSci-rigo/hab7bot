import logging
import uuid

from telegram import Update
from telegram.ext import ContextTypes

from app.ai.agent import run_agent_turn
from app.ai.agent_tools import ToolError, dispatch_tool
from app.bot import state
from app.bot.format import capture_confirmation_text
from app.bot.jobs import run_tick
from app.bot.keyboards import capture_fix_keyboard, confirmation_keyboard, role_picker_keyboard
from app.config import settings
from app.db import SessionLocal
from app.models.enums import Quadrant, TaskOrigin
from app.schemas.task import TaskUpdate
from app.services import capture as capture_service
from app.services import projects as projects_service
from app.services import roles as roles_service
from app.services import tasks as tasks_service
from app.services.clock import now

logger = logging.getLogger(__name__)


def _is_allowed(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user.id == settings.telegram_allowed_user_id)


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    await update.message.reply_text(
        "Compass is online. Send \"add: <task>\" to capture, or just talk to me "
        "about your week. /help for more."
    )


async def help_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update):
        return
    await update.message.reply_text(
        "add: <text> — fast capture, AI-classified, with a fix keyboard\n"
        "Anything else — talk to me conversationally: \"what's on my plate this "
        "week?\", \"break down the garage project\", \"move that to Friday\", "
        "\"mark the dentist task done\".\n"
        "/debug tick — force-fire the morning brief/evening check-in/weekly review/"
        "planning prompt right now, bypassing day/time gating (testing only)."
    )


async def _debug_tick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    with SessionLocal() as db:
        await run_tick(db, context, now(), force=True)
    await update.message.reply_text(
        "Debug tick fired — all four proactive behaviors ran, bypassing day/time/"
        "already-sent gating."
    )


DEBUG_ACTIONS = {"tick": _debug_tick}


async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Owner-only debug commands, e.g. `/debug tick` to force-fire the
    scheduler tick's four behaviors immediately (bypassing all gating) so
    Sunday-only behaviors can be tested without waiting for an actual
    Sunday. Add more subcommands to DEBUG_ACTIONS as needed.
    """
    if not _is_allowed(update):
        return
    args = context.args or []
    if not args or args[0] not in DEBUG_ACTIONS:
        await update.message.reply_text(f"Usage: /debug <{'|'.join(DEBUG_ACTIONS)}>")
        return
    await DEBUG_ACTIONS[args[0]](update, context)


async def handle_message(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update) or not update.message or not update.message.text:
        return
    text = update.message.text.strip()

    if text.lower().startswith("add:"):
        await _handle_capture(update, text[len("add:") :].strip())
        return

    await _handle_agent_turn(update, text)


async def _handle_capture(update: Update, raw_text: str) -> None:
    if not raw_text:
        await update.message.reply_text("Add what? Try \"add: call the dentist\".")
        return
    with SessionLocal() as db:
        task = capture_service.capture_task(db, raw_text, origin=TaskOrigin.telegram)
        role = roles_service.get_role(db, task.role_id) if task.role_id else None
        text = capture_confirmation_text(task, role)
        keyboard = capture_fix_keyboard(task)
    await update.message.reply_text(text, reply_markup=keyboard)


async def _handle_agent_turn(update: Update, text: str) -> None:
    await update.message.chat.send_action("typing")
    with SessionLocal() as db:
        result = run_agent_turn(db, text)

    if result.reply_text:
        await update.message.reply_text(result.reply_text)

    if result.pending_confirmation:
        await _send_confirmation_prompt(update, result.pending_confirmation)


async def _send_confirmation_prompt(update: Update, pending: dict) -> None:
    tool_name = pending["tool_name"]
    args = pending["args"]
    with SessionLocal() as db:
        if tool_name == "drop_task":
            task = tasks_service.get_task(db, uuid.UUID(args["task_id"]))
            label = f'Drop task "{task.title}"?' if task else "Drop this task?"
        elif tool_name == "abandon_project":
            project = projects_service.get_project(db, uuid.UUID(args["project_id"]))
            label = f'Abandon project "{project.title}"?' if project else "Abandon this project?"
        else:
            label = "Confirm this action?"

    token = state.register(pending)
    await update.message.reply_text(label, reply_markup=confirmation_keyboard(token))


async def handle_callback(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return
    if not update.effective_user or update.effective_user.id != settings.telegram_allowed_user_id:
        await query.answer()
        return

    parts = query.data.split(":")
    prefix = parts[0]

    if prefix == "cfx":
        await _handle_capture_fix_callback(query, parts)
    elif prefix == "cfm":
        await _handle_confirmation_callback(query, parts)
    else:
        await query.answer()


async def _handle_capture_fix_callback(query, parts: list[str]) -> None:
    action = parts[1]

    if action == "q":
        _, _, token, quadrant = parts
        task_id = state.resolve(token)
        if task_id is None:
            await query.answer("This has expired.")
            return
        task_id = uuid.UUID(task_id)
        with SessionLocal() as db:
            task = tasks_service.update_task(
                db, task_id, TaskUpdate(quadrant=Quadrant(quadrant))
            )
            role = roles_service.get_role(db, task.role_id) if task.role_id else None
            await query.edit_message_text(
                capture_confirmation_text(task, role), reply_markup=capture_fix_keyboard(task)
            )
        await query.answer(f"Set to {quadrant}")

    elif action == "b":
        _, _, token = parts
        task_id = state.resolve(token)
        if task_id is None:
            await query.answer("This has expired.")
            return
        task_id = uuid.UUID(task_id)
        with SessionLocal() as db:
            task = tasks_service.get_task(db, task_id)
            task = tasks_service.update_task(
                db, task_id, TaskUpdate(is_big_rock=not task.is_big_rock)
            )
            role = roles_service.get_role(db, task.role_id) if task.role_id else None
            await query.edit_message_text(
                capture_confirmation_text(task, role), reply_markup=capture_fix_keyboard(task)
            )
        await query.answer()

    elif action == "r":
        _, _, token = parts
        task_id = state.resolve(token)
        if task_id is None:
            await query.answer("This has expired.")
            return
        with SessionLocal() as db:
            roles = roles_service.list_roles(db, active_only=True)
            await query.edit_message_reply_markup(role_picker_keyboard(token, roles))
        await query.answer()

    elif action == "sr":
        _, _, task_token, role_token = parts
        task_id = state.resolve(task_token)
        role_id = state.resolve(role_token)
        if task_id is None or role_id is None:
            await query.answer("This has expired.")
            return
        task_id = uuid.UUID(task_id)
        role_id = uuid.UUID(role_id)
        with SessionLocal() as db:
            task = tasks_service.update_task(db, task_id, TaskUpdate(role_id=role_id))
            role = roles_service.get_role(db, role_id)
            await query.edit_message_text(
                capture_confirmation_text(task, role), reply_markup=capture_fix_keyboard(task)
            )
        await query.answer(f"Role set to {role.name}")

    elif action == "back":
        _, _, token = parts
        task_id = state.resolve(token)
        if task_id is None:
            await query.answer("This has expired.")
            return
        task_id = uuid.UUID(task_id)
        with SessionLocal() as db:
            task = tasks_service.get_task(db, task_id)
            role = roles_service.get_role(db, task.role_id) if task.role_id else None
            await query.edit_message_text(
                capture_confirmation_text(task, role), reply_markup=capture_fix_keyboard(task)
            )
        await query.answer()


async def _handle_confirmation_callback(query, parts: list[str]) -> None:
    _, decision, token = parts
    pending = state.resolve(token)
    state.discard(token)
    if pending is None:
        await query.answer("This has expired.")
        return

    if decision == "no":
        await query.edit_message_text("Cancelled.")
        await query.answer()
        return

    with SessionLocal() as db:
        try:
            dispatch_tool(db, pending["tool_name"], pending["args"])
            await query.edit_message_text("Done.")
        except ToolError as e:
            await query.edit_message_text(f"Couldn't do that: {e}")
    await query.answer()
