import json
from pathlib import Path
from typing import Optional


SUPPORTED_AGENTS = [
    "claude-code",
    "cursor",
    "codex",
    "gemini-cli",
    "antigravity",
    "custom"
]

SUPPORTED_MODELS = [
    "claude-sonnet-4-6",
    "claude-opus-4-6",
    "gpt-4o",
    "gpt-4-turbo",
    "gemini-3-pro",
    "kimi",
    "custom"
]

SUPPORTED_PROVIDERS = [
    "anthropic",
    "openai",
    "google",
    "moonshot",
    "custom"
]

DEFAULT_CONFIG = {
    "provider": "anthropic",
    "model": "claude-sonnet-4-6",
    "agent": "claude-code",
    "api_key_env": "ANTHROPIC_API_KEY"
}


class Config:

    CONFIG_FILENAME = "config.json"

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.contextos_dir = project_root / ".contextos"
        self.config_path = self.contextos_dir / self.CONFIG_FILENAME
        self._data = {}
        self._load()

    # --- Load ---

    def _load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = DEFAULT_CONFIG.copy()
        else:
            self._data = DEFAULT_CONFIG.copy()

    # --- Save ---

    def _save(self):
        self.contextos_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    # --- Get ---

    def get(self, key: str, fallback=None):
        return self._data.get(key, fallback)

    # --- Set ---

    def set(self, key: str, value: str):
        self._data[key] = value
        self._save()

    # --- All ---

    def all(self) -> dict:
        return self._data.copy()

    # --- Provider display ---

    def get_provider_display(self) -> str:
        provider = self.get("provider", "anthropic")
        displays = {
            "anthropic": "Anthropic",
            "openai": "OpenAI",
            "google": "Google",
            "moonshot": "Moonshot AI",
            "custom": "Custom"
        }
        return displays.get(provider, provider.title())

    def get_agent_display(self) -> str:
        agent = self.get("agent", "claude-code")
        displays = {
            "claude-code": "Claude Code",
            "cursor": "Cursor",
            "codex": "Codex",
            "gemini-cli": "Gemini CLI",
            "antigravity": "Antigravity",
            "custom": "Custom"
        }
        return displays.get(agent, agent.title())

    def get_model_display(self) -> str:
        return self.get("model", "claude-sonnet-4-6")