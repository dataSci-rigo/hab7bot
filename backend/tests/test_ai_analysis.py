import pytest

from app.ai.analysis import analyze_week
from app.ai.schemas import WeekAnalysis


def test_analyze_week_returns_validated_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = {
        "summary": "Solid week, Q2 effort up.",
        "wins": ["Shipped the migration"],
        "concerns": ["Two tasks carried over again"],
        "patterns": ["Q2 effort climbing three weeks running"],
        "suggestions": [
            {
                "change": "Pin the report task as a big rock",
                "why": "It's carried over twice now",
                "how": "Schedule it first thing Monday",
            }
        ],
        "suggested_big_rock_candidates_next_week": ["Quarterly report"],
        "q2_percent_trend": "climbing for the third week",
    }
    monkeypatch.setattr("app.ai.analysis.call_tool", lambda **kwargs: raw)

    result = analyze_week(stats={"iso_week": "2026-W33"}, previous_analyses=[], reflection=None)

    assert isinstance(result, WeekAnalysis)
    assert result.summary == "Solid week, Q2 effort up."
    assert result.q2_percent_trend == "climbing for the third week"


def test_analyze_week_returns_none_when_call_tool_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.ai.analysis.call_tool", lambda **kwargs: None)

    result = analyze_week(stats={}, previous_analyses=[], reflection=None)

    assert result is None


def test_analyze_week_returns_none_on_malformed_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.ai.analysis.call_tool", lambda **kwargs: {"summary": "missing required fields"}
    )

    result = analyze_week(stats={}, previous_analyses=[], reflection=None)

    assert result is None
