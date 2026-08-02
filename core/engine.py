from pathlib import Path
from datetime import datetime
from core.parser import Parser, AICFModel, Task, SubTask
from typing import Optional


class Engine:

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.contextos_dir = self.project_root / ".contextos"
        self.aicf_path = self.contextos_dir / "aicf.json"
        self.parser = Parser(self.aicf_path)
        self._context: Optional[AICFModel] = None

    # --- Load ---

    def load_context(self) -> AICFModel:
        self._context = self.parser.load()
        return self._context

    def save_context(self) -> None:
        if self._context:
            self.parser.save(self._context)

    # --- Read ---

    def get_current_task(self) -> Optional[Task]:
        ctx = self.load_context()
        current_id = ctx.state.current_task
        for task in ctx.tasks:
            if task.id == current_id:
                return task
        return None

    def get_current_subtask(self) -> Optional[SubTask]:
        task = self.get_current_task()
        if not task:
            return None
        ctx = self._context
        current_sub_id = ctx.state.current_subtask
        if not current_sub_id:
            return None
        for sub in task.subtasks:
            if sub.id == current_sub_id:
                return sub
        return None

    def get_next_task(self) -> Optional[Task]:
        ctx = self.load_context()
        for task in ctx.tasks:
            if task.status == "pending":
                return task
        return None

    def get_next_subtask(self) -> Optional[SubTask]:
        task = self.get_current_task()
        if not task:
            return None
        for sub in task.subtasks:
            if sub.status == "pending":
                return sub
        return None

    # --- Update ---

    def update_task_status(self, task_id: str, status: str) -> bool:
        ctx = self.load_context()
        for task in ctx.tasks:
            if task.id == task_id:
                task.status = status
                if status == "done":
                    task.completed_at = datetime.now().isoformat()
                self._context = ctx
                self.save_context()
                return True
            for sub in task.subtasks:
                if sub.id == task_id:
                    sub.status = status
                    if status == "done":
                        sub.completed_at = datetime.now().isoformat()
                    self._context = ctx
                    self.save_context()
                    return True
        return False

    def set_current_task(self, task_id: str) -> bool:
        ctx = self.load_context()
        for task in ctx.tasks:
            if task.id == task_id:
                ctx.state.current_task = task_id
                self._context = ctx
                self.save_context()
                return True
        return False

    def set_current_subtask(self, subtask_id: str) -> bool:
        ctx = self.load_context()
        for task in ctx.tasks:
            for sub in task.subtasks:
                if sub.id == subtask_id:
                    ctx.state.current_subtask = subtask_id
                    self._context = ctx
                    self.save_context()
                    return True
        return False

    # --- Build Prompt ---

    def build_prompt(self, user_input: str) -> str:
        from core.compressor import Compressor

        ctx = self.load_context()
        compressor = Compressor(project_root=self.project_root)
        context_block = compressor.build_compressed_block(ctx)
        return f"{context_block}\n\nUSER REQUEST:\n{user_input}"

    # --- Status ---

    def get_status(self) -> dict:
        ctx = self.load_context()
        task = self.get_current_task()
        subtask = self.get_current_subtask()

        total = len(ctx.tasks)
        done = sum(1 for t in ctx.tasks if t.status == "done")

        return {
            "project": ctx.project.name,
            "goal": ctx.project.goal,
            "phase": ctx.state.phase,
            "current_task": task.title if task else "None",
            "current_subtask": subtask.title if subtask else "None",
            "progress": f"{done}/{total} tasks done",
            "tasks": ctx.tasks
        }