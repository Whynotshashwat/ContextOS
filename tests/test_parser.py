import pytest
import json
from pathlib import Path
from core.parser import Parser, AICFModel


# --- Fixtures ---

@pytest.fixture
def sample_aicf(tmp_path):
    data = {
        "aicf_version": "1.0",
        "project": {
            "name": "TestProject",
            "goal": "Test the parser",
            "description": "A test project"
        },
        "state": {
            "phase": "Testing",
            "current_task": "1",
            "current_subtask": "1.1"
        },
        "tasks": [
            {
                "id": "1",
                "title": "Write tests",
                "status": "in_progress",
                "priority": "high",
                "subtasks": [
                    {
                        "id": "1.1",
                        "title": "Test parser",
                        "status": "pending",
                        "priority": "high"
                    }
                ]
            }
        ],
        "rules": {
            "max_subtasks": 5,
            "execute_one_subtask_only": True,
            "always_use_context": True
        }
    }
    aicf_path = tmp_path / "aicf.json"
    with open(aicf_path, "w") as f:
        json.dump(data, f)
    return aicf_path


# --- Tests ---

def test_parser_loads_valid_aicf(sample_aicf):
    parser = Parser(sample_aicf)
    model = parser.load()
    assert isinstance(model, AICFModel)
    assert model.project.name == "TestProject"
    assert model.project.goal == "Test the parser"


def test_parser_reads_state(sample_aicf):
    parser = Parser(sample_aicf)
    model = parser.load()
    assert model.state.phase == "Testing"
    assert model.state.current_task == "1"
    assert model.state.current_subtask == "1.1"


def test_parser_reads_tasks(sample_aicf):
    parser = Parser(sample_aicf)
    model = parser.load()
    assert len(model.tasks) == 1
    assert model.tasks[0].id == "1"
    assert model.tasks[0].title == "Write tests"
    assert len(model.tasks[0].subtasks) == 1


def test_parser_reads_rules(sample_aicf):
    parser = Parser(sample_aicf)
    model = parser.load()
    assert model.rules.max_subtasks == 5
    assert model.rules.execute_one_subtask_only == True


def test_parser_saves_aicf(sample_aicf):
    parser = Parser(sample_aicf)
    model = parser.load()
    model.project.name = "UpdatedProject"
    parser.save(model)
    reloaded = parser.load()
    assert reloaded.project.name == "UpdatedProject"


def test_parser_raises_on_missing_file(tmp_path):
    parser = Parser(tmp_path / "nonexistent.json")
    with pytest.raises(FileNotFoundError):
        parser.load()


def test_parser_raises_on_invalid_aicf(tmp_path):
    bad_path = tmp_path / "bad.json"
    with open(bad_path, "w") as f:
        json.dump({"invalid": "data"}, f)
    parser = Parser(bad_path)
    with pytest.raises(ValueError):
        parser.load()