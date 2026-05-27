import tiktoken
from pathlib import Path
from typing import Optional, List
from core.parser import AICFModel, Task, SubTask
from core.ignore import IgnoreRules

class Compressor:

    PRIORITY_LIMIT = 800  # max tokens for compressed context

    def __init__(self, project_root:Optional[Path] = None):
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.ignore = IgnoreRules(project_root) if project_root else None

    def filter_paths(self, paths: List[str]) -> List[str]:
        if self.ignore:
            return self.ignore.filter_paths(paths)
        return paths

    # --- Token Counting ---

    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))

    # --- Compression ---

    def compress(self, model: AICFModel) -> dict:
        """
        Priority stack:
        1. current_task + current_subtask
        2. active rules
        3. last 3 decisions (pulled from caller if needed)
        4. pending tasks (titles only)
        5. project goal (single line)
        Drop: completed task details, logs, cache
        """

        compressed = {}

        # Priority 1 — Current state
        compressed["current_task"] = model.state.current_task
        compressed["current_subtask"] = model.state.current_subtask or ""

        # Priority 2 — Active rules
        compressed["rules"] = {
            "execute_one_subtask_only": model.rules.execute_one_subtask_only,
            "always_use_context": model.rules.always_use_context
        }

        # Priority 3 — Pending tasks titles only
        pending = [
            {"id": t.id, "title": t.title}
            for t in model.tasks
            if t.status == "pending"
        ]
        compressed["pending_tasks"] = pending[:5]  # max 5

        # Priority 4 — Project goal
        compressed["project_goal"] = model.project.goal

        # Priority 5 — Phase
        compressed["phase"] = model.state.phase

        return compressed

    # --- Build Compressed Prompt Block ---

    def build_compressed_block(
        self,
        model: AICFModel,
        decisions: Optional[list] = None
    ) -> str:

        c = self.compress(model)

        # Get current task title
        current_task_title = ""
        current_subtask_title = ""
        for task in model.tasks:
            if task.id == c["current_task"]:
                current_task_title = task.title
                for sub in task.subtasks:
                    if sub.id == c["current_subtask"]:
                        current_subtask_title = sub.title

        lines = [
            "=== CONTEXT OS ===",
            f"GOAL: {c['project_goal']}",
            f"PHASE: {c['phase']}",
            f"CURRENT TASK: {current_task_title or c['current_task']}",
        ]

        if current_subtask_title:
            lines.append(
                f"CURRENT SUBTASK: {current_subtask_title}"
            )

        if c["pending_tasks"]:
            pending_titles = ", ".join(
                [t["title"] for t in c["pending_tasks"]]
            )
            lines.append(f"PENDING: {pending_titles}")

        # Last 3 decisions
        if decisions:
            recent = decisions[-3:]
            for d in recent:
                lines.append(
                    f"DECISION [{d['task_id']}]: {d['selected_option']}"
                )

        lines.append("RULES: one subtask at a time")
        lines.append("=================")

        block = "\n".join(lines)
        token_count = self.count_tokens(block)

        # Trim if over limit
        if token_count > self.PRIORITY_LIMIT:
            block = self._trim_to_limit(block)

        return block

    # --- Trim ---

    def _trim_to_limit(self, text: str) -> str:
        tokens = self.encoder.encode(text)
        trimmed = tokens[:self.PRIORITY_LIMIT]
        return self.encoder.decode(trimmed)

    # --- Token Reduction Stats ---

    def get_reduction_stats(
        self,
        original: str,
        compressed: str
    ) -> dict:
        original_tokens = self.count_tokens(original)
        compressed_tokens = self.count_tokens(compressed)
        reduction = original_tokens - compressed_tokens
        percentage = (
            round((reduction / original_tokens) * 100, 1)
            if original_tokens > 0 else 0
        )
        return {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "tokens_saved": reduction,
            "reduction_percentage": f"{percentage}%"
        }