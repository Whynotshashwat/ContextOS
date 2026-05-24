from typing import List, Optional
from datetime import datetime
from core.parser import Task, SubTask


class Decomposer:

    MAX_SUBTASKS = 5

    # --- Main Decompose ---

    def decompose(
        self,
        task: Task,
        subtask_titles: List[str]
    ) -> Task:
        """
        Takes a task and a list of subtask titles.
        Returns the task with subtasks attached.
        Max 5 subtasks enforced.
        """

        if len(subtask_titles) > self.MAX_SUBTASKS:
            subtask_titles = subtask_titles[:self.MAX_SUBTASKS]

        subtasks = []
        for i, title in enumerate(subtask_titles):
            sub = SubTask(
                id=f"{task.id}.{i + 1}",
                title=title,
                status="pending",
                priority=task.priority,
                created_at=datetime.now().isoformat()
            )
            subtasks.append(sub)

        task.subtasks = subtasks
        return task

    # --- Auto Suggest Subtasks ---

    def suggest_subtasks(self, task_title: str) -> List[str]:
        """
        Rule-based subtask suggestions.
        Returns suggested subtask titles based on keywords.
        """

        title_lower = task_title.lower()

        # Authentication
        if any(k in title_lower for k in ["auth", "login", "signup"]):
            return [
                "Create login UI",
                "Validate credentials",
                "Create auth middleware",
                "Add session handling",
                "Add logout support"
            ]

        # API
        if any(k in title_lower for k in ["api", "endpoint", "route"]):
            return [
                "Define API schema",
                "Create route handlers",
                "Add input validation",
                "Add error handling",
                "Write API tests"
            ]

        # Database
        if any(k in title_lower for k in ["database", "db", "model", "schema"]):
            return [
                "Define data models",
                "Create migrations",
                "Add CRUD operations",
                "Add indexes",
                "Test database operations"
            ]

        # UI
        if any(k in title_lower for k in ["ui", "frontend", "page", "component"]):
            return [
                "Create component structure",
                "Add styling",
                "Add state management",
                "Connect to API",
                "Test UI interactions"
            ]

        # Testing
        if any(k in title_lower for k in ["test", "testing", "spec"]):
            return [
                "Write unit tests",
                "Write integration tests",
                "Add test fixtures",
                "Run test suite",
                "Fix failing tests"
            ]

        # Setup
        if any(k in title_lower for k in ["setup", "init", "install", "config"]):
            return [
                "Create project structure",
                "Install dependencies",
                "Configure environment",
                "Add configuration files",
                "Verify setup"
            ]

        # Documentation
        if any(k in title_lower for k in ["doc", "readme", "guide"]):
            return [
                "Write overview section",
                "Document installation steps",
                "Document usage examples",
                "Add API reference",
                "Review and publish"
            ]

        # Default generic subtasks
        return [
            "Research and plan",
            "Implement core logic",
            "Add error handling",
            "Write tests",
            "Review and refine"
        ]

    # --- Validate Decomposition ---

    def validate_decomposition(self, task: Task) -> tuple:
        errors = []

        if len(task.subtasks) == 0:
            errors.append(
                f"Task {task.id} has no subtasks"
            )

        if len(task.subtasks) > self.MAX_SUBTASKS:
            errors.append(
                f"Task {task.id} exceeds max subtasks limit of {self.MAX_SUBTASKS}"
            )

        for sub in task.subtasks:
            if not sub.title.strip():
                errors.append(
                    f"Subtask {sub.id} has empty title"
                )

        return len(errors) == 0, errors

    # --- Get Next Pending Subtask ---

    def get_next_pending(
        self,
        task: Task
    ) -> Optional[SubTask]:
        for sub in task.subtasks:
            if sub.status == "pending":
                return sub
        return None

    # --- Check Task Complete ---

    def is_task_complete(self, task: Task) -> bool:
        if not task.subtasks:
            return task.status == "done"
        return all(
            sub.status == "done"
            for sub in task.subtasks
        )