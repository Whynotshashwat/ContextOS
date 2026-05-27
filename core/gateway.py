from typing import Optional
from pathlib import Path
from core.engine import Engine
from core.compressor import Compressor
from core.memory import Memory
from core.validator import Validator


class Gateway:

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.contextos_dir = self.project_root / ".contextos"
        self.engine = Engine(self.project_root)
        self.compressor = Compressor(project_root=self.project_root)
        self.memory = Memory(self.contextos_dir)
        self.validator = Validator()

    # --- Main Inject ---

    def inject(
        self,
        user_prompt: str,
        override_context: Optional[dict] = None
    ) -> str:
        """
        Main entry point.
        Takes user prompt.
        Returns prompt with compressed context injected.
        """

        # Load context
        model = self.engine.load_context()

        # Validate
        is_valid, errors = self.validator.validate_aicf(model)
        if not is_valid:
            raise ValueError(
                f"Invalid context:\n" + "\n".join(errors)
            )

        # Get decisions
        decisions = self.memory.get_decisions()

        # Build compressed block
        context_block = self.compressor.build_compressed_block(
            model,
            decisions=decisions
        )

        # Apply overrides if provided
        if override_context:
            context_block = self._apply_overrides(
                context_block,
                override_context
            )

        # Build final prompt
        final_prompt = self._build_final_prompt(
            context_block,
            user_prompt
        )

        # Log interaction
        self.memory.log(
            f"Prompt injected | tokens: "
            f"{self.compressor.count_tokens(final_prompt)}"
        )

        # Save snapshot before interaction
        self.memory.take_snapshot(
            self.engine.parser.load_raw(),
            label="pre_interaction"
        )

        return final_prompt

    # --- Build Final Prompt ---

    def _build_final_prompt(
        self,
        context_block: str,
        user_prompt: str
    ) -> str:
        return f"{context_block}\n\nUSER REQUEST:\n{user_prompt}"

    # --- Apply Overrides ---

    def _apply_overrides(
        self,
        context_block: str,
        overrides: dict
    ) -> str:
        for key, value in overrides.items():
            context_block += f"\nOVERRIDE {key.upper()}: {value}"
        return context_block

    # --- Explain ---

    def explain(
        self,
        task_id: Optional[str] = None
    ) -> str:
        """
        Shows exactly what context would be injected
        without actually sending anything.
        Implements context explain command.
        """

        model = self.engine.load_context()

        # Temporarily override current task if provided
        if task_id:
            self.engine._context = model
            self.engine.set_current_task(task_id)
            model = self.engine.load_context()

        decisions = self.memory.get_decisions()

        context_block = self.compressor.build_compressed_block(
            model,
            decisions=decisions
        )

        token_count = self.compressor.count_tokens(context_block)
        score = self.validator.context_score(model)

        explanation = (
            f"\n=== CONTEXT EXPLAIN ===\n"
            f"{context_block}\n"
            f"\nContext Score : {score}/100"
            f"\nToken Count   : {token_count} tokens"
            f"\n=======================\n"
        )

        return explanation

    # --- Get Stats ---

    def get_stats(self, raw_codebase: str = "") -> dict:
        model = self.engine.load_context()
        decisions = self.memory.get_decisions()

        compressed_block = self.compressor.build_compressed_block(
            model,
            decisions=decisions
        )

        stats = {
            "context_score": self.validator.context_score(model),
            "compressed_tokens": self.compressor.count_tokens(
                compressed_block
            )
        }

        if raw_codebase:
            stats["reduction"] = self.compressor.get_reduction_stats(
                raw_codebase,
                compressed_block
            )

        return stats