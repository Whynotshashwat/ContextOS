import pytest
import json
from pathlib import Path
from core.stats import Stats


# --- Fixtures ---

@pytest.fixture
def project(tmp_path):
    contextos_dir = tmp_path / ".contextos"
    contextos_dir.mkdir()
    logs_dir = contextos_dir / "logs"
    logs_dir.mkdir()
    snapshots_dir = contextos_dir / "snapshots"
    snapshots_dir.mkdir()

    data = {
        "aicf_version": "1.0",
        "project": {
            "name": "TestProject",
            "goal": "Test stats",
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
                "title": "Setup project",
                "status": "done",
                "priority": "high",
                "subtasks": [
                    {
                        "id": "1.1",
                        "title": "Create structure",
                        "status": "done",
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

    (contextos_dir / "memory.json").write_text(json.dumps({
        "snapshots": [
            {
                "id": "snap_001",
                "label": "test snap",
                "timestamp": "2026-05-24T06:00:00"
            }
        ],
        "compressed_history": [],
        "last_compressed": None
    }))

    (contextos_dir / "decisions.json").write_text(json.dumps({
        "decisions": [
            {
                "id": "d1",
                "task_id": "1",
                "selected_option": "B",
                "rationale": "user selected",
                "timestamp": "2026-05-24T06:00:00"
            }
        ]
    }))

    # Write a log file with interactions
    log_file = logs_dir / "2026-05-24.log"
    log_file.write_text(
        "[2026-05-24 06:00:00] [INFO] Prompt injected | tokens: 58\n"
        "[2026-05-24 06:01:00] [INFO] Prompt injected | tokens: 45\n"
    )

    return tmp_path


# --- Tests ---

def test_stats_initializes(project):
    stats = Stats(project)
    assert stats is not None


def test_stats_returns_dict(project):
    stats = Stats(project)
    data = stats.get_stats()
    assert isinstance(data, dict)


def test_stats_project_name(project):
    stats = Stats(project)
    data = stats.get_stats()
    assert data["project"] == "TestProject"


def test_stats_context_score(project):
    stats = Stats(project)
    data = stats.get_stats()
    assert 0 <= data["context_score"] <= 100


def test_stats_counts_interactions(project):
    stats = Stats(project)
    data = stats.get_stats()
    assert data["interactions"] == 2


def test_stats_counts_tokens(project):
    stats = Stats(project)
    data = stats.get_stats()
    assert data["total_tokens_injected"] == 103


def test_stats_counts_decisions(project):
    stats = Stats(project)
    data = stats.get_stats()
    assert data["decisions_recorded"] == 1


def test_stats_counts_snapshots(project):
    stats = Stats(project)
    data = stats.get_stats()
    assert data["snapshots_saved"] == 1


def test_stats_counts_completed_tasks(project):
    stats = Stats(project)
    data = stats.get_stats()
    assert data["tasks_completed"] == 1


def test_stats_counts_completed_subtasks(project):
    stats = Stats(project)
    data = stats.get_stats()
    assert data["subtasks_completed"] == 1


def test_stats_without_baseline(project):
    stats = Stats(project)
    data = stats.get_stats()
    assert "baseline_tokens" not in data
    assert "estimated_reduction" not in data


def test_stats_with_baseline(project):
    stats = Stats(project)
    data = stats.get_stats(baseline_tokens=4000)
    assert "baseline_tokens" in data
    assert "estimated_tokens_saved" in data
    assert "estimated_reduction" in data
    assert data["baseline_tokens"] == 4000
    assert "baseline_note" in data


def test_stats_format_returns_string(project):
    stats = Stats(project)
    data = stats.get_stats()
    formatted = stats.format_stats(data)
    assert isinstance(formatted, str)
    assert "ContextOS Stats" in formatted
    assert "TestProject" in formatted


def test_stats_format_with_baseline(project):
    stats = Stats(project)
    data = stats.get_stats(baseline_tokens=4000)
    formatted = stats.format_stats(data)
    assert "baseline" in formatted.lower()
    assert "4000" in formatted