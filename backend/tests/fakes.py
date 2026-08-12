"""Fakes for a faked-model-client test style (record/replay), per CLAUDE.md
ground rule 9 — used to test the agent tool loop without hitting the live
Anthropic API."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeTextBlock:
    text: str
    type: str = "text"

    def model_dump(self) -> dict:
        return {"type": "text", "text": self.text}


@dataclass
class FakeToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]
    type: str = "tool_use"

    def model_dump(self) -> dict:
        return {"type": "tool_use", "id": self.id, "name": self.name, "input": self.input}


@dataclass
class FakeMessage:
    content: list[Any] = field(default_factory=list)


class FakeModelClient:
    """Queue of canned responses returned in order, one per call to
    `create_message`. Monkeypatch `app.ai.agent.create_message` with an
    instance's `__call__`."""

    def __init__(self, responses: list[FakeMessage | None]):
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> FakeMessage | None:
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("FakeModelClient ran out of canned responses")
        return self._responses.pop(0)
