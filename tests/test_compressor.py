import pytest
import json
from pathlib import Path
from core.compressor import Compressor
from core.parser import AICFModel, ProjectModel, StateModel, RulesModel, Task, SubTask


# --- Fixtures ---

@pytest.fixture
def sample_model():
    return AICFModel(
        aicf_version="1.0",
        project=ProjectModel(
            name="TestProject",
            goal="Test the compressor",
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
            ),
            Task(
                id="2",
                title="Build core",
                status="pending",
                priority="high",
                subtasks=[]
            ),
            Task(
                id="3",
                title="Write tests",
                status="done",
                priority="medium",
                subtasks=[]
            )
        ],
        rules=RulesModel(
            max_subtasks=5,
            execute_one_subtask_only=True,
            always_use_context=True
        )
    )


# --- Tests ---

def test_compressor_initializes():
    compressor = Compressor()
    assert compressor is not None
    assert compressor.encoder is not None


def test_count_tokens():
    compressor = Compressor()
    tokens = compressor.count_tokens("Hello world")
    assert isinstance(tokens, int)
    assert tokens > 0


def test_compress_returns_dict(sample_model):
    compressor = Compressor()
    result = compressor.compress(sample_model)
    assert isinstance(result, dict)
    assert "current_task" in result
    assert "current_subtask" in result
    assert "rules" in result
    assert "pending_tasks" in result
    assert "project_goal" in result


def test_compress_excludes_done_tasks(sample_model):
    compressor = Compressor()
    result = compressor.compress(sample_model)
    pending_titles = [t["title"] for t in result["pending_tasks"]]
    assert "Write tests" not in pending_titles


def test_compress_includes_pending_tasks(sample_model):
    compressor = Compressor()
    result = compressor.compress(sample_model)
    pending_titles = [t["title"] for t in result["pending_tasks"]]
    assert "Build core" in pending_titles


def test_build_compressed_block_returns_string(sample_model):
    compressor = Compressor()
    block = compressor.build_compressed_block(sample_model)
    assert isinstance(block, str)
    assert len(block) > 0


def test_compressed_block_contains_goal(sample_model):
    compressor = Compressor()
    block = compressor.build_compressed_block(sample_model)
    assert "Test the compressor" in block


def test_compressed_block_contains_task(sample_model):
    compressor = Compressor()
    block = compressor.build_compressed_block(sample_model)
    assert "Setup project" in block


def test_compressed_block_under_token_limit(sample_model):
    compressor = Compressor()
    block = compressor.build_compressed_block(sample_model)
    tokens = compressor.count_tokens(block)
    assert tokens <= compressor.PRIORITY_LIMIT


def test_reduction_stats(sample_model):
    compressor = Compressor()
    original = "word " * 500
    compressed = compressor.build_compressed_block(sample_model)
    stats = compressor.get_reduction_stats(original, compressed)
    assert "original_tokens" in stats
    assert "compressed_tokens" in stats
    assert "tokens_saved" in stats
    assert "reduction_percentage" in stats
    assert stats["tokens_saved"] > 0


def test_decisions_in_compressed_block(sample_model):
    compressor = Compressor()
    decisions = [
        {"task_id": "1", "selected_option": "B"},
        {"task_id": "2", "selected_option": "A"}
    ]
    block = compressor.build_compressed_block(
        sample_model,
        decisions=decisions
    )
    assert "DECISION" in block