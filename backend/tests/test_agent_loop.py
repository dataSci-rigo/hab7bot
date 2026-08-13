import uuid

import pytest
from sqlalchemy.orm import Session

from app.ai.agent import run_agent_turn
from app.ai.agent_tools import dispatch_tool
from app.models.enums import TaskStatus
from app.schemas.role import RoleCreate
from app.services import roles as roles_service
from app.services import tasks as tasks_service
from tests.fakes import FakeMessage, FakeModelClient, FakeTextBlock, FakeToolUseBlock


@pytest.fixture()
def role(db_session: Session):
    return roles_service.create_role(db_session, RoleCreate(name="Engineer"))


def test_plain_text_reply_no_tools(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeModelClient([FakeMessage([FakeTextBlock("Sure, what's up?")])])
    monkeypatch.setattr("app.ai.agent.create_message", fake)

    result = run_agent_turn(db_session, "hey")

    assert result.reply_text == "Sure, what's up?"
    assert result.pending_confirmation is None
    assert len(fake.calls) == 1


def test_conversation_history_persisted(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeModelClient([FakeMessage([FakeTextBlock("Hi there")])])
    monkeypatch.setattr("app.ai.agent.create_message", fake)

    run_agent_turn(db_session, "hello")

    from app.services import conversation as conversation_service

    history = conversation_service.get_recent_messages(db_session)
    assert [(m.role, m.content) for m in history] == [
        ("user", "hello"),
        ("assistant", "Hi there"),
    ]


def test_tool_call_then_text_reply(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    dispatch_tool(
        db_session,
        "create_task",
        {"title": "Ship v1", "role_name": "Engineer", "scheduled_week": "2026-W32"},
    )
    fake = FakeModelClient(
        [
            FakeMessage([FakeToolUseBlock("t1", "get_week_plan", {"iso_week": "2026-W32"})]),
            FakeMessage([FakeTextBlock("You have 1 task scheduled: Ship v1.")]),
        ]
    )
    monkeypatch.setattr("app.ai.agent.create_message", fake)

    result = run_agent_turn(db_session, "what's on my plate this week?")

    assert result.reply_text == "You have 1 task scheduled: Ship v1."
    assert len(fake.calls) == 2
    # second call's message history should include the tool_result the loop generated
    second_call_messages = fake.calls[1]["messages"]
    tool_result_msg = next(
        m
        for m in second_call_messages
        if m["role"] == "user" and isinstance(m["content"], list)
    )
    assert "Ship v1" in tool_result_msg["content"][0]["content"]


def test_chained_tool_calls_across_iterations(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = dispatch_tool(
        db_session, "create_task", {"title": "Call the dentist", "role_name": "Engineer"}
    )

    fake = FakeModelClient(
        [
            FakeMessage([FakeToolUseBlock("t1", "search_tasks", {"query": "dentist"})]),
            FakeMessage(
                [
                    FakeToolUseBlock(
                        "t2",
                        "update_task",
                        {"task_id": created["id"], "scheduled_week": "2026-W40"},
                    )
                ]
            ),
            FakeMessage([FakeTextBlock("Moved it to week 40.")]),
        ]
    )
    monkeypatch.setattr("app.ai.agent.create_message", fake)

    result = run_agent_turn(db_session, "reschedule the dentist task to week 40")

    assert result.reply_text == "Moved it to week 40."
    assert len(fake.calls) == 3
    task = tasks_service.get_task(db_session, uuid.UUID(created["id"]))
    assert task.scheduled_week == "2026-W40"


def test_complete_task_via_agent(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = dispatch_tool(
        db_session, "create_task", {"title": "Finish report", "role_name": "Engineer"}
    )
    fake = FakeModelClient(
        [
            FakeMessage([FakeToolUseBlock("t1", "complete_task", {"task_id": created["id"]})]),
            FakeMessage([FakeTextBlock("Marked done!")]),
        ]
    )
    monkeypatch.setattr("app.ai.agent.create_message", fake)

    result = run_agent_turn(db_session, "mark the report task done")

    assert result.reply_text == "Marked done!"
    task = tasks_service.get_task(db_session, uuid.UUID(created["id"]))
    assert task.status == TaskStatus.done


def test_drop_task_requires_confirmation_and_does_not_execute(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = dispatch_tool(
        db_session, "create_task", {"title": "Old idea", "role_name": "Engineer"}
    )
    fake = FakeModelClient(
        [
            FakeMessage([FakeToolUseBlock("t1", "drop_task", {"task_id": created["id"]})]),
            FakeMessage([FakeTextBlock("I'll wait for you to confirm dropping that.")]),
        ]
    )
    monkeypatch.setattr("app.ai.agent.create_message", fake)

    result = run_agent_turn(db_session, "drop the old idea task")

    assert result.pending_confirmation == {
        "tool_name": "drop_task",
        "args": {"task_id": created["id"]},
    }
    # not actually dropped yet — confirmation is a separate step (see bot handlers)
    task = tasks_service.get_task(db_session, uuid.UUID(created["id"]))
    assert task.status != TaskStatus.dropped

    # simulate the user tapping "Confirm" in Telegram
    dispatch_tool(db_session, "drop_task", {"task_id": created["id"]})
    task = tasks_service.get_task(db_session, uuid.UUID(created["id"]))
    assert task.status == TaskStatus.dropped


def test_breakdown_project_tool_via_agent(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = dispatch_tool(
        db_session, "create_project", {"title": "Migrate DB", "role_name": "Engineer"}
    )
    fake_proposal = {
        "milestones": [
            {"title": "Plan", "tasks": [{"title": "Audit schema", "quadrant": "Q2"}]}
        ],
        "assumptions": [],
        "questions": [],
    }
    from app.ai.schemas import BreakdownProposal

    monkeypatch.setattr(
        "app.ai.agent_tools.ai_breakdown_project",
        lambda db, pid: BreakdownProposal.model_validate(fake_proposal),
    )
    fake = FakeModelClient(
        [
            FakeMessage(
                [FakeToolUseBlock("t1", "breakdown_project", {"project_id": project["id"]})]
            ),
            FakeMessage([FakeTextBlock("Here's a proposal: Audit schema. Want me to add it?")]),
        ]
    )
    monkeypatch.setattr("app.ai.agent.create_message", fake)

    result = run_agent_turn(db_session, "break down the migrate db project")

    assert "Audit schema" in result.reply_text
    # nothing written yet — ground rule 3
    tasks = tasks_service.list_tasks(db_session, project_id=uuid.UUID(project["id"]))
    assert tasks == []


def test_ai_unavailable_degrades_gracefully(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeModelClient([None])
    monkeypatch.setattr("app.ai.agent.create_message", fake)

    result = run_agent_turn(db_session, "hello?")

    assert "trouble reaching the AI" in result.reply_text
    from app.services import conversation as conversation_service

    history = conversation_service.get_recent_messages(db_session)
    assert history[-1].role == "assistant"


def test_max_iterations_fallback(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = dispatch_tool(db_session, "create_task", {"title": "A", "role_name": "Engineer"})
    # model keeps calling a tool forever, never produces a text-only reply
    responses = [
        FakeMessage([FakeToolUseBlock(f"t{i}", "complete_task", {"task_id": created["id"]})])
        for i in range(10)
    ]
    fake = FakeModelClient(responses)
    monkeypatch.setattr("app.ai.agent.create_message", fake)

    result = run_agent_turn(db_session, "loop forever")

    assert result.reply_text
    assert len(fake.calls) == 6  # MAX_TOOL_ITERATIONS


def test_leading_proactive_assistant_message_is_dropped_before_first_user_reply(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A scheduled job (morning brief, evening check-in, Sunday planning
    prompt) can push the very first message in conversation history as an
    assistant turn. The Anthropic API requires the first message to be
    role="user" — regression test for the agent.py fix that trims any
    leading assistant messages before replaying history.
    """
    from app.services import conversation as conversation_service

    conversation_service.append_message(db_session, "assistant", "Good morning! Anything to add?")

    fake = FakeModelClient([FakeMessage([FakeTextBlock("Got it.")])])
    monkeypatch.setattr("app.ai.agent.create_message", fake)

    result = run_agent_turn(db_session, "just the usual")

    assert result.reply_text == "Got it."
    sent_messages = fake.calls[0]["messages"]
    assert sent_messages[0]["role"] == "user"
