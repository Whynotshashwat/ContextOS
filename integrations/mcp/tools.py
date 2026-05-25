from pathlib import Path
from core.engine import Engine
from core.memory import Memory
from core.gateway import Gateway
from core.validator import Validator
from core.stats import Stats
from core.decomposer import Decomposer
from core.suggester import Suggester
from utils.helpers import get_contextos_dir, find_project_root


def get_project_root() -> Path:
    root = find_project_root()
    if not root:
        raise ValueError("No ContextOS project found. Run 'context init' first.")
    return root


def tool_get_current_task() -> dict:
    """Get the current active task and subtask."""
    root = get_project_root()
    engine = Engine(root)
    task = engine.get_current_task()
    subtask = engine.get_current_subtask()
    return {
        "current_task": task.model_dump() if task else None,
        "current_subtask": subtask.model_dump() if subtask else None
    }


def tool_get_next_task() -> dict:
    """Get the next pending task."""
    root = get_project_root()
    engine = Engine(root)
    task = engine.get_next_task()
    subtask = engine.get_next_subtask()
    return {
        "next_task": task.model_dump() if task else None,
        "next_subtask": subtask.model_dump() if subtask else None
    }


def tool_get_status() -> dict:
    """Get full project status."""
    root = get_project_root()
    engine = Engine(root)
    validator = Validator()
    model = engine.load_context()
    status = engine.get_status()
    score = validator.context_score(model)
    return {
        "project": status["project"],
        "goal": status["goal"],
        "phase": status["phase"],
        "current_task": status["current_task"],
        "current_subtask": status["current_subtask"],
        "progress": status["progress"],
        "context_score": score
    }


def tool_get_context(user_prompt: str) -> str:
    """Get compressed context injection for a prompt."""
    root = get_project_root()
    gateway = Gateway(root)
    return gateway.inject(user_prompt)


def tool_explain_context() -> str:
    """Show what context would be injected."""
    root = get_project_root()
    gateway = Gateway(root)
    return gateway.explain()


def tool_mark_done(task_id: str) -> dict:
    """Mark a task or subtask as done."""
    root = get_project_root()
    engine = Engine(root)
    memory = Memory(get_contextos_dir(root))
    memory.take_snapshot(
        engine.parser.load_raw(),
        label=f"before_done_{task_id}"
    )
    success = engine.update_task_status(task_id, "done")
    return {
        "success": success,
        "task_id": task_id,
        "message": f"Task {task_id} marked as done" if success else f"Task {task_id} not found"
    }


def tool_decompose_task(task_id: str) -> dict:
    """Break a task into subtasks."""
    root = get_project_root()
    engine = Engine(root)
    model = engine.load_context()
    decomposer = Decomposer()
    for task in model.tasks:
        if task.id == task_id:
            suggestions = decomposer.suggest_subtasks(task.title)
            task = decomposer.decompose(task, suggestions)
            for t in model.tasks:
                if t.id == task_id:
                    t.subtasks = task.subtasks
                    break
            engine._context = model
            engine.save_context()
            return {
                "task_id": task_id,
                "subtasks": [s.model_dump() for s in task.subtasks]
            }
    return {"error": f"Task {task_id} not found"}


def tool_get_suggestions(task_id: str) -> dict:
    """Get A/B/C implementation suggestions for a task."""
    root = get_project_root()
    engine = Engine(root)
    model = engine.load_context()
    suggester = Suggester()
    for task in model.tasks:
        if task.id == task_id:
            return suggester.suggest(task.title, model)
    return {"error": f"Task {task_id} not found"}


def tool_record_decision(task_id: str, option: str, rationale: str = "") -> dict:
    """Record an A/B/C decision for a task."""
    root = get_project_root()
    memory = Memory(get_contextos_dir(root))
    suggester = Suggester()
    selection = suggester.record_selection(task_id, option)
    memory.add_decision(
        task_id=task_id,
        selected_option=option.upper(),
        rationale=rationale or "claude-code selected"
    )
    return selection


def tool_get_stats() -> dict:
    """Get project statistics."""
    root = get_project_root()
    stats = Stats(root)
    return stats.get_stats()


def tool_take_snapshot(label: str = "") -> dict:
    """Save a context snapshot."""
    root = get_project_root()
    engine = Engine(root)
    memory = Memory(get_contextos_dir(root))
    snapshot_id = memory.take_snapshot(
        engine.parser.load_raw(),
        label=label
    )
    return {"snapshot_id": snapshot_id, "label": label}


def tool_get_decisions() -> list:
    """Get all recorded decisions."""
    root = get_project_root()
    memory = Memory(get_contextos_dir(root))
    return memory.get_decisions()