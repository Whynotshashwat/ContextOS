import pytest
import json
from pathlib import Path
from core.gateway import Gateway
from core.memory import Memory


# --- Fixtures ---

@pytest.fixture
def project(tmp_path):
    contextos_dir = tmp_path / ".contextos"
    contextos_dir.mkdir()

    data = {
        "aicf_version": "1.0",
        "project": {
            "name": "TestProject",
            "goal": "Test the gateway",
            "description": "A test project"
        },
        "state": {
            "phase": "Testing",
            "current_task": "1",
            "current_subtask": ""
        },
        "tasks": [
            {
                "id": "1",
                "title": "Setup project",
                "status": "in_progress",
                "priority": "high",
                "subtasks": [
                    {
                        "id": "1.1",
                        "title": "Create structure",
                        "status": "pending",
                        "priority": "high"
                    }
                ]
            },
            {
                "id": "2",
                "title": "Build core",
                "status": "pending",
                "priority": "high",
                "subtasks": []
            }
        ],
        "rules": {
            "max_subtasks": 5,
            "execute_one_subtask_only": True,
            "always_use_context": True
        }
    }

    (contextos_dir / "aicf.json").write_text(
        json.dumps(data),
        encoding="utf-8"
    )

    return tmp_path


# --- Tests ---

def test_gateway_inject_returns_prompt(project):
    gateway = Gateway(project)
    prompt = gateway.inject("Do something")
    assert isinstance(prompt, str)
    assert "Do something" in prompt
    assert "TestProject" in prompt or "Test the gateway" in prompt


def test_gateway_explain_does_not_mutate_state(project):
    gateway = Gateway(project)
    gateway.explain("2")

    with open(project / ".contextos" / "aicf.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["state"]["current_task"] == "1"


def test_gateway_explain_shows_requested_task(project):
    gateway = Gateway(project)
    explanation = gateway.explain("2")
    assert "Build core" in explanation


def test_gateway_inject_adds_to_history(project):
    gateway = Gateway(project)
    gateway.inject("Do something")
    memory = Memory(project / ".contextos")
    history = memory.get_history()
    assert len(history) == 1
    assert history[0]["type"] == "interaction"
    assert "token_count" in history[0]


def test_gateway_inject_raises_on_invalid_aicf(tmp_path):
    contextos_dir = tmp_path / ".contextos"
    contextos_dir.mkdir()
    (contextos_dir / "aicf.json").write_text(
        json.dumps({
            "aicf_version": "1.0",
            "project": {"name": "", "goal": ""},
            "state": {"phase": "", "current_task": ""},
            "tasks": [],
            "rules": {"max_subtasks": 5}
        }),
        encoding="utf-8"
    )
    gateway = Gateway(tmp_path)
    with pytest.raises(ValueError):
        gateway.inject("Do something")
