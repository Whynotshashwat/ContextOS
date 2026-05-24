from pathlib import Path
from core.engine import Engine
from core.gateway import Gateway
from core.memory import Memory
from core.suggester import Suggester
from core.decomposer import Decomposer
from core.validator import Validator
from utils.helpers import get_contextos_dir


class ContextOS:

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.engine = Engine(self.project_root)
        self.gateway = Gateway(self.project_root)
        self.memory = Memory(get_contextos_dir(self.project_root))
        self.suggester = Suggester()
        self.decomposer = Decomposer()
        self.validator = Validator()

    # --- Context ---

    def inject(self, prompt: str) -> str:
        """Inject compressed context into prompt."""
        return self.gateway.inject(prompt)

    def explain(self, task_id: str = None) -> str:
        """Preview context injection."""
        return self.gateway.explain(task_id)

    def status(self) -> dict:
        """Get current project status."""
        return self.engine.get_status()

    def score(self) -> int:
        """Get context score."""
        model = self.engine.load_context()
        return self.validator.context_score(model)

    # --- Tasks ---

    def next_task(self) -> dict:
        """Get next pending task."""
        task = self.engine.get_next_task()
        if not task:
            return {}
        return task.model_dump()

    def next_subtask(self) -> dict:
        """Get next pending subtask."""
        sub = self.engine.get_next_subtask()
        if not sub:
            return {}
        return sub.model_dump()

    def done(self, task_id: str) -> bool:
        """Mark task or subtask as done."""
        return self.engine.update_task_status(task_id, "done")

    def decompose(self, task_id: str) -> list:
        """Decompose task into subtasks."""
        model = self.engine.load_context()
        for task in model.tasks:
            if task.id == task_id:
                suggestions = self.decomposer.suggest_subtasks(task.title)
                task = self.decomposer.decompose(task, suggestions)
                self.engine._context = model
                self.engine.save_context()
                return [s.model_dump() for s in task.subtasks]
        return []

    # --- Suggestions ---

    def suggest(self, task_id: str) -> dict:
        """Get A/B/C suggestions for a task."""
        model = self.engine.load_context()
        for task in model.tasks:
            if task.id == task_id:
                return self.suggester.suggest(task.title, model)
        return {}

    def decide(self, task_id: str, option: str) -> dict:
        """Record A/B/C decision."""
        selection = self.suggester.record_selection(task_id, option)
        self.memory.add_decision(
            task_id=task_id,
            selected_option=option.upper(),
            rationale="sdk selected"
        )
        return selection

    # --- Memory ---

    def snapshot(self, label: str = "") -> str:
        """Save context snapshot."""
        return self.memory.take_snapshot(
            self.engine.parser.load_raw(),
            label=label
        )

    def rollback(self) -> bool:
        """Restore last snapshot."""
        snapshots = self.memory.get_snapshots()
        if not snapshots:
            return False
        latest = snapshots[-1]
        aicf_data = self.memory.restore_snapshot(latest["id"])
        if not aicf_data:
            return False
        self.engine.parser.save(
            self.engine.parser.load()
        )
        return True

    def decisions(self) -> list:
        """Get all recorded decisions."""
        return self.memory.get_decisions()

    # --- Stats ---

    def stats(self) -> dict:
        """Get token reduction stats."""
        return self.gateway.get_stats()