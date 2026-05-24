from typing import Optional
from core.parser import AICFModel


class Suggester:

    # --- Main Suggest ---

    def suggest(
        self,
        task_title: str,
        context: Optional[AICFModel] = None
    ) -> dict:
        """
        Generates A/B/C implementation approaches
        for a given task.
        """

        return {
            "task": task_title,
            "suggestions": {
                "A": self._safe_approach(task_title),
                "B": self._optimized_approach(task_title),
                "C": self._advanced_approach(task_title)
            },
            "recommended": "B"
        }

    # --- Approaches ---

    def _safe_approach(self, task_title: str) -> dict:
        return {
            "label": "Safe",
            "description": f"Simple and stable implementation of {task_title}",
            "pros": [
                "Easy to implement",
                "Low risk",
                "Easy to debug",
                "Familiar patterns"
            ],
            "cons": [
                "May not scale well",
                "Limited flexibility",
                "Basic architecture"
            ],
            "complexity": "Low",
            "time_estimate": "Short",
            "risk": "Low"
        }

    def _optimized_approach(self, task_title: str) -> dict:
        return {
            "label": "Optimized",
            "description": f"Balanced architecture for {task_title}",
            "pros": [
                "Good performance",
                "Maintainable code",
                "Moderate scalability",
                "Industry standard patterns"
            ],
            "cons": [
                "Moderate complexity",
                "Requires planning",
                "More initial setup"
            ],
            "complexity": "Medium",
            "time_estimate": "Moderate",
            "risk": "Medium"
        }

    def _advanced_approach(self, task_title: str) -> dict:
        return {
            "label": "Advanced",
            "description": f"Scalable and future-proof implementation of {task_title}",
            "pros": [
                "Highly scalable",
                "Maximum flexibility",
                "Production ready",
                "Future proof"
            ],
            "cons": [
                "High complexity",
                "Longer implementation",
                "Requires expertise",
                "Over-engineering risk"
            ],
            "complexity": "High",
            "time_estimate": "Long",
            "risk": "Medium-High"
        }

    # --- Format Output ---

    def format_suggestions(self, suggestions: dict) -> str:
        lines = [
            f"\n=== SUGGESTIONS FOR: {suggestions['task']} ===\n"
        ]

        for key, s in suggestions["suggestions"].items():
            lines.append(f"[{key}] {s['label']} Approach")
            lines.append(f"    {s['description']}")
            lines.append(f"    Complexity : {s['complexity']}")
            lines.append(f"    Time       : {s['time_estimate']}")
            lines.append(f"    Risk       : {s['risk']}")
            lines.append(f"    Pros       : {', '.join(s['pros'][:2])}")
            lines.append(f"    Cons       : {', '.join(s['cons'][:2])}")
            lines.append("")

        lines.append(
            f"Recommended: [{suggestions['recommended']}] "
            f"{suggestions['suggestions'][suggestions['recommended']]['label']}"
        )
        lines.append("=" * 40)

        return "\n".join(lines)

    # --- Record Selection ---

    def record_selection(
        self,
        task_id: str,
        selected: str
    ) -> dict:
        if selected.upper() not in ["A", "B", "C"]:
            raise ValueError(
                f"Invalid selection: {selected}. Must be A, B or C"
            )
        return {
            "task_id": task_id,
            "selected": selected.upper(),
            "rationale": "user selected"
        }