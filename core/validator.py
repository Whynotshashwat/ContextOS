from pathlib import Path
from typing import Tuple, List
from core.parser import AICFModel, Task
import re


class Validator:

    # --- AICF Validation ---

    def validate_aicf(self, model: AICFModel) -> Tuple[bool, List[str]]:
        errors = []

        # Project checks
        if not model.project.name.strip():
            errors.append("Project name is empty")
        if not model.project.goal.strip():
            errors.append("Project goal is empty")

        # State checks
        if not model.state.phase.strip():
            errors.append("Project phase is empty")

        # Task checks
        for task in model.tasks:
            task_errors = self.validate_task(task)
            errors.extend(task_errors)

        # Rules checks
        if model.rules.max_subtasks < 1:
            errors.append("max_subtasks must be at least 1")
        if model.rules.max_subtasks > 10:
            errors.append("max_subtasks cannot exceed 10")

        return len(errors) == 0, errors

    # --- Task Validation ---

    def validate_task(self, task: Task) -> List[str]:
        errors = []

        if not task.id.strip():
            errors.append(f"Task missing id")
        if not task.title.strip():
            errors.append(f"Task {task.id} has empty title")
        if task.status not in ["pending", "in_progress", "done", "blocked"]:
            errors.append(
                f"Task {task.id} has invalid status: {task.status}"
            )
        if task.priority not in ["low", "medium", "high"]:
            errors.append(
                f"Task {task.id} has invalid priority: {task.priority}"
            )

        # Subtask checks
        if len(task.subtasks) > 5:
            errors.append(
                f"Task {task.id} exceeds maximum subtask limit of 5"
            )
        for sub in task.subtasks:
            sub_errors = self.validate_task(sub)
            errors.extend(sub_errors)

        return errors

    # --- File Validation ---

    def validate_contextos_dir(self, contextos_dir: Path) -> Tuple[bool, List[str]]:
        errors = []
        required_files = [
            "aicf.json",
            "memory.json",
            "decisions.json"
        ]
        required_dirs = [
            "snapshots",
            "logs"
        ]

        for file in required_files:
            if not (contextos_dir / file).exists():
                errors.append(f"Missing required file: {file}")

        for dir in required_dirs:
            if not (contextos_dir / dir).exists():
                errors.append(f"Missing required directory: {dir}")

        return len(errors) == 0, errors

    # --- Context Score ---

    def context_score(self, model: AICFModel) -> int:
        score = 0

        # Project completeness
        if model.project.name.strip():
            score += 15
        if model.project.goal.strip():
            score += 20
        if model.project.description.strip():
            score += 10

        # State completeness
        if model.state.phase.strip():
            score += 10
        if model.state.current_task.strip():
            score += 15
        if model.state.current_subtask and \
                model.state.current_subtask.strip():
            score += 10

        # Tasks completeness
        if len(model.tasks) > 0:
            score += 10
        has_subtasks = any(
            len(t.subtasks) > 0 for t in model.tasks
        )
        if has_subtasks:
            score += 10

        return min(score, 100)
    
    
    def validate_task_id(self, task_id: str) -> bool:
        """Only allow alphanumeric, dots and hyphens in task IDs."""
        return bool(re.match(r'^[a-zA-Z0-9.\-]+$', task_id))