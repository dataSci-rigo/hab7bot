"""Tiny in-memory token registry for inline-keyboard callback_data.

Telegram caps callback_data at 64 bytes — too small to embed a task_id and
a role_id UUID in the same button. Instead we hand out short opaque tokens
that map back to real values (task ids, pending confirmations) kept in
process memory. This is intentionally not persisted: a bot restart loses
any in-flight fix/confirmation keyboards, which just means the user taps a
stale button and gets "that's expired, try again" — an acceptable trade-off
for a single-user bot (see DECISIONS.md).
"""
import uuid
from typing import Any

_registry: dict[str, Any] = {}


def register(value: Any) -> str:
    token = uuid.uuid4().hex[:10]
    _registry[token] = value
    return token


def resolve(token: str) -> Any | None:
    return _registry.get(token)


def discard(token: str) -> None:
    _registry.pop(token, None)
