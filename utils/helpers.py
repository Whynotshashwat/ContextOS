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
    with open(path, "r") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def safe_read_json(path: Path) -> Optional[dict]:
    try:
        return read_json(path)
    except Exception:
        return None


# --- String Helpers ---

def truncate(text: str, max_length: int = 50) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def slugify(text: str) -> str:
    return text.lower().strip().replace(" ", "_")


def timestamp() -> str:
    return datetime.now().isoformat()


def friendly_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --- Task Helpers ---

def generate_task_id(existing_ids: list) -> str:
    """
    Generates next available task id.
    Example: if [1, 2, 3] exists, returns 4
    """
    if not existing_ids:
        return "1"
    numeric = []
    for id in existing_ids:
        try:
            numeric.append(int(id.split(".")[0]))
        except ValueError:
            continue
    if not numeric:
        return "1"
    return str(max(numeric) + 1)


def generate_subtask_id(task_id: str, existing_subs: list) -> str:
    """
    Generates next subtask id under a task.
    Example: task 2 with subs [2.1, 2.2] returns 2.3
    """
    if not existing_subs:
        return f"{task_id}.1"
    indices = []
    for sub in existing_subs:
        try:
            parts = sub.id.split(".")
            if len(parts) >= 2:
                indices.append(int(parts[-1]))
        except (ValueError, AttributeError):
            continue
    if not indices:
        return f"{task_id}.1"
    return f"{task_id}.{max(indices) + 1}"


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
        contextos_dir / "logs",
        contextos_dir / "cache"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return contextos_dir