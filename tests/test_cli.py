import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from cli.main import cli


# --- Fixtures ---

@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def project(tmp_path):
    contextos_dir = tmp_path / ".contextos"
    contextos_dir.mkdir()

    data = {
        "aicf_version": "1.0",
        "project": {
            "name": "TestProject",
            "goal": "Test the CLI",
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

    (contextos_dir / "memory.json").write_text(json.dumps({
        "snapshots": [],
        "compressed_history": [],
        "last_compressed": None
    }))
    (contextos_dir / "decisions.json").write_text(json.dumps({
        "decisions": []
    }))
    (contextos_dir / "snapshots").mkdir()
    (contextos_dir / "logs").mkdir()

    return tmp_path


# --- Tests ---

def test_cli_help(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "ContextOS" in result.output


def test_cli_init(runner, tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, [
            "init", "TestProject", "Test the CLI"
        ])
        assert result.exit_code == 0
        assert "initialized" in result.output.lower()


def test_cli_status(runner, project):
    with runner.isolated_filesystem(temp_dir=project):
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "TestProject" in result.output


def test_cli_next(runner, project):
    with runner.isolated_filesystem(temp_dir=project):
        result = runner.invoke(cli, ["next"])
        assert result.exit_code == 0


def test_cli_done(runner, project):
    with runner.isolated_filesystem(temp_dir=project):
        result = runner.invoke(cli, ["done", "1.1"])
        assert result.exit_code == 0
        assert "done" in result.output.lower()


def test_cli_done_dry_run(runner, project):
    with runner.isolated_filesystem(temp_dir=project):
        result = runner.invoke(cli, ["done", "1.1", "--dry-run"])
        assert result.exit_code == 0
        assert "dry run" in result.output.lower()


def test_cli_goal(runner, project):
    with runner.isolated_filesystem(temp_dir=project):
        result = runner.invoke(cli, ["goal", "New goal"])
        assert result.exit_code == 0
        assert "updated" in result.output.lower()


def test_cli_decompose(runner, project):
    with runner.isolated_filesystem(temp_dir=project):
        result = runner.invoke(cli, ["decompose", "2"])
        assert result.exit_code == 0
        assert "decomposed" in result.output.lower()


def test_cli_decompose_dry_run(runner, project):
    with runner.isolated_filesystem(temp_dir=project):
        result = runner.invoke(cli, ["decompose", "2", "--dry-run"])
        assert result.exit_code == 0
        assert "dry run" in result.output.lower()


def test_cli_explain(runner, project):
    with runner.isolated_filesystem(temp_dir=project):
        result = runner.invoke(cli, ["explain"])
        assert result.exit_code == 0
        assert "CONTEXT" in result.output


def test_cli_snapshot(runner, project):
    with runner.isolated_filesystem(temp_dir=project):
        result = runner.invoke(cli, ["snapshot", "test-snap"])
        assert result.exit_code == 0
        assert "snapshot" in result.output.lower()


def test_cli_rollback(runner, project):
    with runner.isolated_filesystem(temp_dir=project):
        # Take snapshot first
        runner.invoke(cli, ["snapshot", "before-rollback"])
        result = runner.invoke(cli, ["rollback"])
        assert result.exit_code == 0


def test_cli_done_invalid_task(runner, project):
    with runner.isolated_filesystem(temp_dir=project):
        result = runner.invoke(cli, ["done", "99"])
        assert result.exit_code == 0
        assert "not found" in result.output.lower()