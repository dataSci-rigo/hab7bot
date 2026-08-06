import json
from pathlib import Path

from app.ai.schemas import (
    BreakdownProposal,
    CaptureInference,
    InboxTriageOutput,
    ProjectSuggestionsOutput,
)

FIXTURES = Path(__file__).parent / "fixtures" / "ai"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_breakdown_fixture_matches_schema() -> None:
    proposal = BreakdownProposal.model_validate(_load("breakdown.json"))
    assert len(proposal.milestones) > 0
    assert all(m.tasks for m in proposal.milestones)
    assert all(t.quadrant for m in proposal.milestones for t in m.tasks)


def test_suggestions_fixture_matches_schema() -> None:
    output = ProjectSuggestionsOutput.model_validate(_load("suggestions.json"))
    assert 1 <= len(output.suggestions) <= 5
    for suggestion in output.suggestions:
        assert suggestion.title
        assert suggestion.role_name
        assert len(suggestion.first_three_tasks) == 3


def test_capture_fixture_matches_schema() -> None:
    inference = CaptureInference.model_validate(_load("capture.json"))
    assert inference.title
    assert inference.role_name == "Engineer"


def test_inbox_triage_fixture_matches_schema() -> None:
    output = InboxTriageOutput.model_validate(_load("inbox_triage.json"))
    assert len(output.items) == 2
    assert {item.task_id for item in output.items} == {
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    }
