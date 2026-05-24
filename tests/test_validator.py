import pytest
from pathlib import Path
from core.validator import Validator
from core.parser import AICFModel, ProjectModel, StateModel, RulesModel, Task, SubTask


# --- Fixtures ---

@pytest.fixture
def valid_model():
    return AICFModel(
        aicf_version="1.0",
        project=ProjectModel(
            name="TestProject",
            goal="Test the validator",
            description="A test project"
        ),
        state=StateModel(
            phase="Testing",
            current_task="1",
            current_subtask="1.1"
        ),
        tasks=[
            Task(
                id="1",
                title="Setup project",
                status="in_progress",
                priority="high",
                subtasks=[
                    SubTask(
                        id="1.1",
                        title="Create structure",
                        status="pending",
                        priority="high"
                    )
                ]
            )
        ],
        rules=RulesModel(
            max_subtasks=5,
            execute_one_subtask_only=True,
            always_use_context=True
        )
    )


@pytest.fixture
def invalid_model():
    return AICFModel(
        aicf_version="1.0",
        project=ProjectModel(
            name="",
            goal="",
            description=""
        ),
        state=StateModel(
            phase="",
            current_task="",
            current_subtask=""
        ),
        tasks=[],
        rules=RulesModel(
            max_subtasks=5,
            execute_one_subtask_only=True,
            always_use_context=True
        )
    )


# --- Validation Tests ---

def test_valid_model_passes(valid_model):
    validator = Validator()
    is_valid, errors = validator.validate_aicf(valid_model)
    assert is_valid == True
    assert len(errors) == 0


def test_empty_name_fails(invalid_model):
    validator = Validator()
    is_valid, errors = validator.validate_aicf(invalid_model)
    assert is_valid == False
    assert any("name" in e.lower() for e in errors)


def test_empty_goal_fails(invalid_model):
    validator = Validator()
    is_valid, errors = validator.validate_aicf(invalid_model)
    assert is_valid == False
    assert any("goal" in e.lower() for e in errors)


def test_empty_phase_fails(invalid_model):
    validator = Validator()
    is_valid, errors = validator.validate_aicf(invalid_model)
    assert is_valid == False
    assert any("phase" in e.lower() for e in errors)


def test_valid_task_passes(valid_model):
    validator = Validator()
    errors = validator.validate_task(valid_model.tasks[0])
    assert len(errors) == 0


def test_invalid_task_status_fails():
    validator = Validator()
    task = Task(
        id="1",
        title="Bad task",
        status="unknown",
        priority="high"
    )
    errors = validator.validate_task(task)
    assert len(errors) > 0
    assert any("status" in e.lower() for e in errors)


def test_invalid_task_priority_fails():
    validator = Validator()
    task = Task(
        id="1",
        title="Bad task",
        status="pending",
        priority="critical"
    )
    errors = validator.validate_task(task)
    assert len(errors) > 0
    assert any("priority" in e.lower() for e in errors)


# --- Context Score Tests ---

def test_context_score_full_model(valid_model):
    validator = Validator()
    score = validator.context_score(valid_model)
    assert isinstance(score, int)
    assert 0 <= score <= 100
    assert score >= 70


def test_context_score_empty_model(invalid_model):
    validator = Validator()
    score = validator.context_score(invalid_model)
    assert score < 50


def test_context_score_never_exceeds_100(valid_model):
    validator = Validator()
    score = validator.context_score(valid_model)
    assert score <= 100


# --- Directory Validation Tests ---

def test_valid_contextos_dir(tmp_path):
    validator = Validator()
    contextos_dir = tmp_path / ".contextos"
    contextos_dir.mkdir()

    # Create required files
    (contextos_dir / "aicf.json").touch()
    (contextos_dir / "memory.json").touch()
    (contextos_dir / "decisions.json").touch()
    (contextos_dir / "snapshots").mkdir()
    (contextos_dir / "logs").mkdir()

    is_valid, errors = validator.validate_contextos_dir(contextos_dir)
    assert is_valid == True
    assert len(errors) == 0


def test_missing_files_in_contextos_dir(tmp_path):
    validator = Validator()
    contextos_dir = tmp_path / ".contextos"
    contextos_dir.mkdir()

    is_valid, errors = validator.validate_contextos_dir(contextos_dir)
    assert is_valid == False
    assert len(errors) > 0