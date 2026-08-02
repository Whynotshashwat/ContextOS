import pytest
import json
from pathlib import Path
from sdk.python.contextos_sdk import ContextOS


# --- Fixtures ---

@pytest.fixture
def project(tmp_path):
    contextos_dir = tmp_path / ".contextos"
    contextos_dir.mkdir()

    data = {
        "aicf_version": "1.0",
        "project": {
            "name": "TestProject",
            "goal": "Original goal",
            "description": ""
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

def test_rollback_restores_content(project):
    sdk = ContextOS(project)

    # Snapshot the original state
    sdk.snapshot("original")

    # Modify the goal
    model = sdk.engine.load_context()
    model.project.goal = "Changed goal"
    sdk.engine.save_context()

    assert sdk.rollback() is True

    model = sdk.engine.load_context()
    assert model.project.goal == "Original goal"


def test_rollback_returns_false_when_no_snapshots(project):
    sdk = ContextOS(project)
    assert sdk.rollback() is False


def test_decompose_adds_subtasks(project):
    sdk = ContextOS(project)
    subtasks = sdk.decompose("1")
    assert len(subtasks) > 0
    model = sdk.engine.load_context()
    assert len(model.tasks[0].subtasks) == len(subtasks)


def test_done_marks_task(project):
    sdk = ContextOS(project)
    assert sdk.done("1") is True
    model = sdk.engine.load_context()
    assert model.tasks[0].status == "done"


def test_status_returns_dict(project):
    sdk = ContextOS(project)
    status = sdk.status()
    assert status["project"] == "TestProject"
