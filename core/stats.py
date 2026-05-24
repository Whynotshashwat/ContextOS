import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from core.memory import Memory
from core.validator import Validator
from core.compressor import Compressor
from core.engine import Engine


class Stats:

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.contextos_dir = project_root / ".contextos"
        self.engine = Engine(project_root)
        self.memory = Memory(self.contextos_dir)
        self.validator = Validator()
        self.compressor = Compressor()
        self.log_dir = self.contextos_dir / "logs"

    # --- Core Stats ---

    def get_stats(self, baseline_tokens: Optional[int] = None) -> dict:
        """
        Returns honest stats based on actual recorded data.
        Optionally accepts a user-provided baseline for reduction calc.
        """
        model = self.engine.load_context()
        decisions = self.memory.get_decisions()
        snapshots = self.memory.get_snapshots()

        # Count completed tasks
        completed_tasks = sum(
            1 for t in model.tasks
            if t.status == "done"
        )
        completed_subtasks = sum(
            1 for t in model.tasks
            for s in t.subtasks
            if s.status == "done"
        )

        # Count interactions from logs
        interactions = self._count_interactions()

        # Count total tokens injected from logs
        total_tokens = self._count_total_tokens()

        # Current context token count
        compressed_block = self.compressor.build_compressed_block(
            model,
            decisions=decisions
        )
        current_tokens = self.compressor.count_tokens(compressed_block)

        # Context score
        score = self.validator.context_score(model)

        stats = {
            "project": model.project.name,
            "context_score": score,
            "interactions": interactions,
            "total_tokens_injected": total_tokens,
            "current_context_tokens": current_tokens,
            "decisions_recorded": len(decisions),
            "snapshots_saved": len(snapshots),
            "tasks_completed": completed_tasks,
            "subtasks_completed": completed_subtasks,
            "total_tasks": len(model.tasks),
        }

        # Only add reduction if user provides baseline
        if baseline_tokens and baseline_tokens > 0:
            if interactions > 0:
                estimated_raw = baseline_tokens * interactions
                estimated_saved = estimated_raw - total_tokens
                reduction_pct = round(
                    (estimated_saved / estimated_raw) * 100, 1
                ) if estimated_raw > 0 else 0
                stats["baseline_tokens"] = baseline_tokens
                stats["estimated_raw_tokens"] = estimated_raw
                stats["estimated_tokens_saved"] = estimated_saved
                stats["estimated_reduction"] = f"{reduction_pct}%"
                stats["baseline_note"] = "Based on user-provided baseline"

        return stats

    # --- Count Interactions ---

    def _count_interactions(self) -> int:
        """Count actual AI interactions from log files."""
        count = 0
        if not self.log_dir.exists():
            return 0
        for log_file in self.log_dir.glob("*.log"):
            with open(log_file, "r") as f:
                for line in f:
                    if "Prompt injected" in line:
                        count += 1
        return count

    # --- Count Total Tokens ---

    def _count_total_tokens(self) -> int:
        """Count total tokens injected from log files."""
        total = 0
        if not self.log_dir.exists():
            return 0
        for log_file in self.log_dir.glob("*.log"):
            with open(log_file, "r") as f:
                for line in f:
                    if "tokens:" in line:
                        try:
                            token_part = line.split("tokens:")[-1].strip()
                            total += int(token_part)
                        except ValueError:
                            continue
        return total

    # --- Format Output ---

    def format_stats(self, stats: dict) -> str:
        lines = [
            "\n╭──────────── ContextOS Stats ────────────╮"
        ]

        lines.append(
            f"│ Project               : {stats['project']:<20}│"
        )
        lines.append(
            f"│ Context Score         : {str(stats['context_score']) + '/100':<20}│"
        )
        lines.append(
            f"│ {'─' * 38} │"
        )
        lines.append(
            f"│ Total interactions    : {str(stats['interactions']):<20}│"
        )
        lines.append(
            f"│ Total tokens injected : {str(stats['total_tokens_injected']):<20}│"
        )
        lines.append(
            f"│ Current context size  : {str(stats['current_context_tokens']) + ' tokens':<20}│"
        )
        lines.append(
            f"│ {'─' * 38} │"
        )
        lines.append(
            f"│ Decisions recorded    : {str(stats['decisions_recorded']):<20}│"
        )
        lines.append(
            f"│ Snapshots saved       : {str(stats['snapshots_saved']):<20}│"
        )
        lines.append(
            f"│ Tasks completed       : {str(stats['tasks_completed']):<20}│"
        )
        lines.append(
            f"│ Subtasks completed    : {str(stats['subtasks_completed']):<20}│"
        )

        # Only show reduction if baseline provided
        if "baseline_tokens" in stats:
            lines.append(f"│ {'─' * 38} │")
            lines.append(
                f"│ Your baseline         : {str(stats['baseline_tokens']) + ' tokens':<20}│"
            )
            lines.append(
                f"│ Est. tokens saved     : {str(stats['estimated_tokens_saved']):<20}│"
            )
            lines.append(
                f"│ Est. reduction        : {stats['estimated_reduction']:<20}│"
            )
            lines.append(
                f"│ * {stats['baseline_note']:<36} │"
            )

        lines.append(
            "╰─────────────────────────────────────────╯"
        )

        return "\n".join(lines)