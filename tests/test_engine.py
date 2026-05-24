import pytest
import json
from pathlib import Path
from core.engine import Engine


# --- Fixtures ---

@pytest.fixture
def project(tmp_path):
    contextos_dir = tmp_path / ".contextos"
    contextos_dir.mkdir()

    data = {
        "aicf_version": "1.0",
        "project": {
            "name": "TestProject",
            "goal": "Test the engine",
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
                    },
                    {
                        "id": "1.2",
                        "title": "Install deps",
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

    aicf_path = contextos_dir / "aicf.json"
    with open(aicf_path, "w") as f:
        json.dump(data, f)

    return tmp_path


# --- Tests ---

def test_engine_loads_context(project):
    engine = Engine(project)
    model = engine.load_context()
    assert model.project.name == "TestProject"


def test_engine_get_current_task(project):
    engine = Engine(project)
    task = engine.get_current_task()
    assert task is not None
    assert task.id == "1"
    assert task.title == "Setup project"


def test_engine_get_next_task(project):
    engine = Engine(project)
    task = engine.get_next_task()
    assert task is not None
    assert task.id == "2"
    assert task.status == "pending"


def test_engine_get_next_subtask(project):
    engine = Engine(project)
    sub = engine.get_next_subtask()
    assert sub is not None
    assert sub.id == "1.1"
    assert sub.status == "pending"


def test_engine_update_task_status(project):
    engine = Engine(project)
    result = engine.update_task_status("1.1", "done")
    assert result == True
    model = engine.load_context()
    sub = model.tasks[0].subtasks[0]
    assert sub.status == "done"
    assert sub.completed_at is not None


def test_engine_update_invalid_task(project):
    engine = Engine(project)
    result = engine.update_task_status("99", "done")
    assert result == False


def test_engine_set_current_task(project):
    engine = Engine(project)
    engine.set_current_task("2")
    model = engine.load_context()
    assert model.state.current_task == "2"


def test_engine_set_current_subtask(project):
    engine = Engine(project)
    engine.set_current_subtask("1.1")
    model = engine.load_context()
    assert model.state.current_subtask == "1.1"


def test_engine_build_prompt(project):
    engine = Engine(project)
    prompt = engine.build_prompt("Do something")
    assert "TestProject" in prompt or "Test the engine" in prompt
    assert "Do something" in prompt


def test_engine_get_status(project):
    engine = Engine(project)
    status = engine.get_status()
    assert status["project"] == "TestProject"
    assert status["current_task"] == "Setup project"
    assert "progress" in status