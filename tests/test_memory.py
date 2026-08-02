import pytest
from pathlib import Path
from core.memory import Memory


# --- Fixtures ---

@pytest.fixture
def contextos_dir(tmp_path):
    dir = tmp_path / ".contextos"
    dir.mkdir()
    return dir


@pytest.fixture
def memory(contextos_dir):
    return Memory(contextos_dir)


# --- Snapshot Tests ---

def test_snapshot_ids_unique_in_same_second(memory):
    id1 = memory.take_snapshot({"project": {"name": "A"}}, "first")
    id2 = memory.take_snapshot({"project": {"name": "B"}}, "second")
    assert id1 != id2


def test_snapshot_files_written(memory):
    snap_id = memory.take_snapshot({"project": {"name": "A"}}, "test")
    assert (memory.snapshots_dir / f"{snap_id}.json").exists()


def test_snapshot_registered_in_memory_json(memory):
    before = len(memory.get_snapshots())
    memory.take_snapshot({"project": {"name": "A"}}, "test")
    after = memory.get_snapshots()
    assert len(after) == before + 1


def test_restore_snapshot_returns_aicf(memory):
    aicf_data = {"project": {"name": "RestoreMe"}}
    snap_id = memory.take_snapshot(aicf_data, "test")
    restored = memory.restore_snapshot(snap_id)
    assert restored == aicf_data


def test_restore_unknown_snapshot_returns_none(memory):
    assert memory.restore_snapshot("snap_nonexistent") is None


# --- Decision Tests ---

def test_add_decision_appends(memory):
    memory.add_decision("1", "B", "user selected")
    decisions = memory.get_decisions()
    assert len(decisions) == 1
    assert decisions[0]["task_id"] == "1"
    assert decisions[0]["selected_option"] == "B"


def test_get_decisions_for_task(memory):
    memory.add_decision("1", "B")
    memory.add_decision("2", "A")
    task_decisions = memory.get_decisions_for_task("1")
    assert len(task_decisions) == 1
    assert task_decisions[0]["task_id"] == "1"


# --- History Tests ---

def test_add_to_history(memory):
    memory.add_to_history({"type": "interaction", "token_count": 10})
    history = memory.get_history()
    assert len(history) == 1
    assert history[0]["token_count"] == 10
    assert "timestamp" in history[0]
