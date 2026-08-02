import json
from pathlib import Path
from datetime import datetime
from typing import Optional


# --- Path Helpers ---

def find_project_root(start: Path = None) -> Optional[Path]:
    """
    Walk up directory tree to find .contextos folder.
    Returns project root if found, None otherwise.
    """
    current = start or Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".contextos").exists():
            return parent
    return None


def get_contextos_dir(project_root: Path) -> Path:
    return project_root / ".contextos"


def get_aicf_path(project_root: Path) -> Path:
    return project_root / ".contextos" / "aicf.json"


# --- JSON Helpers ---

def read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def friendly_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --- Status Helpers ---

def status_color(status: str) -> str:
    colors = {
        "pending": "yellow",
        "in_progress": "cyan",
        "done": "green",
        "blocked": "red"
    }
    return colors.get(status, "white")


def priority_color(priority: str) -> str:
    colors = {
        "low": "green",
        "medium": "yellow",
        "high": "red"
    }
    return colors.get(priority, "white")


# --- Contextos Dir Setup ---

def setup_contextos_dir(project_root: Path) -> Path:
    """
    Creates .contextos directory structure.
    Returns path to .contextos dir.
    """
    contextos_dir = project_root / ".contextos"
    dirs = [
        contextos_dir,
        contextos_dir / "snapshots",
        contextos_dir / "logs"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return contextos_dir