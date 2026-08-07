from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot import state
from app.models.role import Role
from app.models.task import Task

QUADRANTS = ["Q1", "Q2", "Q3", "Q4"]


def capture_fix_keyboard(task: Task) -> InlineKeyboardMarkup:
    token = state.register(str(task.id))
    quadrant_row = [
        InlineKeyboardButton(
            ("✓ " if task.quadrant.value == q else "") + q, callback_data=f"cfx:q:{token}:{q}"
        )
        for q in QUADRANTS
    ]
    star = "⭐ Big rock" if not task.is_big_rock else "⭐ Unpin big rock"
    action_row = [
        InlineKeyboardButton(star, callback_data=f"cfx:b:{token}"),
        InlineKeyboardButton("Role ▾", callback_data=f"cfx:r:{token}"),
    ]
    return InlineKeyboardMarkup([quadrant_row, action_row])


def role_picker_keyboard(task_token: str, roles: list[Role]) -> InlineKeyboardMarkup:
    rows = []
    for role in roles:
        role_token = state.register(str(role.id))
        rows.append(
            [InlineKeyboardButton(role.name, callback_data=f"cfx:sr:{task_token}:{role_token}")]
        )
    rows.append([InlineKeyboardButton("‹ Back", callback_data=f"cfx:back:{task_token}")])
    return InlineKeyboardMarkup(rows)


def confirmation_keyboard(token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Confirm", callback_data=f"cfm:yes:{token}"),
                InlineKeyboardButton("Cancel", callback_data=f"cfm:no:{token}"),
            ]
        ]
    )
