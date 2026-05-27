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

# --- Ignore Integration Tests ---

@pytest.fixture
def project_with_ignore(tmp_path):
    """Project root with a .contextosignore file."""
    ignore_file = tmp_path / ".contextosignore"
    ignore_file.write_text("""# Test ignore
.venv/
__pycache__/
*.pyc
*.log
node_modules/
""")
    return tmp_path


def test_compressor_initializes_without_project_root():
    compressor = Compressor()
    assert compressor.ignore is None


def test_compressor_initializes_with_project_root(project_with_ignore):
    compressor = Compressor(project_root=project_with_ignore)
    assert compressor.ignore is not None


def test_filter_paths_no_project_root():
    compressor = Compressor()
    paths = ["core/engine.py", ".venv/lib/site.py", "__pycache__/x.pyc"]
    result = compressor.filter_paths(paths)
    assert result == paths  # nothing filtered — no rules loaded


def test_filter_paths_with_ignore(project_with_ignore):
    compressor = Compressor(project_root=project_with_ignore)
    paths = [
        "core/engine.py",
        ".venv/lib/site.py",
        "__pycache__/engine.pyc",
        "cli/main.py",
        "logs/2026-05-25.log"
    ]
    result = compressor.filter_paths(paths)
    assert "core/engine.py" in result
    assert "cli/main.py" in result
    assert ".venv/lib/site.py" not in result
    assert "__pycache__/engine.pyc" not in result
    assert "logs/2026-05-25.log" not in result


def test_filter_paths_returns_all_when_no_match(project_with_ignore):
    compressor = Compressor(project_root=project_with_ignore)
    paths = ["core/engine.py", "sdk/python/contextos_sdk.py", "README.md"]
    result = compressor.filter_paths(paths)
    assert result == paths


def test_compressor_build_block_unaffected_by_ignore(
    sample_model, project_with_ignore
):
    """Confirm compressed block still builds correctly when project_root set."""
    compressor = Compressor(project_root=project_with_ignore)
    block = compressor.build_compressed_block(sample_model)
    assert isinstance(block, str)
    assert "Test the compressor" in block
    assert compressor.count_tokens(block) <= compressor.PRIORITY_LIMIT