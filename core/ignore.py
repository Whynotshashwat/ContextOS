from pathlib import Path
from typing import List


class IgnoreRules:

    IGNORE_FILENAME = ".contextosignore"
    DEFAULT_RULES = [
        ".venv/",
        "__pycache__/",
        "*.pyc",
        "*.log",
        "node_modules/",
        ".git/",
        "dist/",
        "build/",
        "*.egg-info/"
    ]

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ignore_file = project_root / self.IGNORE_FILENAME
        self.rules: List[str] = []
        self._load()

    # --- Load ---

    def _load(self):
        if self.ignore_file.exists():
            with open(self.ignore_file, "r") as f:
                lines = f.readlines()
            self.rules = [
                line.strip()
                for line in lines
                if line.strip() and not line.startswith("#")
            ]
        else:
            self.rules = self.DEFAULT_RULES.copy()

    # --- Create Default ---

    def create_default(self) -> Path:
        """Creates a default .contextosignore file."""
        content = """# ContextOS Ignore File
# Files and folders listed here will never be included in context

# Dependencies
.venv/
node_modules/

# Build artifacts
__pycache__/
*.pyc
*.pyo
dist/
build/
*.egg-info/

# Logs
*.log
logs/

# Version control
.git/

# Environment
.env
config.json

# Test artifacts
.pytest_cache/
.coverage
"""
        with open(self.ignore_file, "w") as f:
            f.write(content)
        return self.ignore_file

    # --- Check ---

    def is_ignored(self, path: str) -> bool:
        """Check if a path matches any ignore rule."""
        path = path.replace("\\", "/")
        for rule in self.rules:
            rule = rule.rstrip("/")
            # Directory rule
            if rule.endswith("/") or "/" not in rule:
                if rule.rstrip("/") in path:
                    return True
            # Wildcard rule
            if rule.startswith("*"):
                ext = rule[1:]
                if path.endswith(ext):
                    return True
            # Exact match
            if path == rule or path.endswith("/" + rule):
                return True
        return False

    # --- Filter ---

    def filter_paths(self, paths: List[str]) -> List[str]:
        """Filter a list of paths removing ignored ones."""
        return [p for p in paths if not self.is_ignored(p)]

    # --- List Rules ---

    def list_rules(self) -> List[str]:
        return self.rules

    # --- Add Rule ---

    def add_rule(self, rule: str):
        if rule not in self.rules:
            self.rules.append(rule)
            self._save()

    # --- Remove Rule ---

    def remove_rule(self, rule: str):
        if rule in self.rules:
            self.rules.remove(rule)
            self._save()

    # --- Save ---

    def _save(self):
        existing = []
        comments = []
        if self.ignore_file.exists():
            with open(self.ignore_file, "r") as f:
                lines = f.readlines()
            comments = [l for l in lines if l.startswith("#") or l.strip() == ""]
            existing = [l.strip() for l in lines if l.strip() and not l.startswith("#")]

        with open(self.ignore_file, "w") as f:
            for c in comments:
                f.write(c)
            for rule in self.rules:
                if rule not in existing:
                    f.write(f"{rule}\n")