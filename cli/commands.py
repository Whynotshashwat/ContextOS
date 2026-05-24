import json
import shutil
from pathlib import Path
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from core.engine import Engine
from core.memory import Memory
from core.validator import Validator
from core.suggester import Suggester
from core.decomposer import Decomposer
from core.gateway import Gateway
from utils.helpers import (
    find_project_root,
    get_contextos_dir,
    get_aicf_path,
    setup_contextos_dir,
    write_json,
    read_json,
    generate_task_id,
    generate_subtask_id,
    status_color,
    priority_color,
    friendly_timestamp
)
from utils.logger import logger

console = Console()


# --- Init ---

def cmd_init(project_name: str, goal: str):
    project_root = Path.cwd()
    contextos_dir = setup_contextos_dir(project_root)

    # Load default template
    template_path = (
        Path(__file__).parent.parent /
        "templates" /
        "default_context.json"
    )
    aicf_data = read_json(template_path)

    # Fill in project details
    aicf_data["project"]["name"] = project_name
    aicf_data["project"]["goal"] = goal
    aicf_data["state"]["current_task"] = "1"

    # Write aicf.json
    aicf_path = contextos_dir / "aicf.json"
    write_json(aicf_path, aicf_data)

    # Init memory and decisions
    memory = Memory(contextos_dir)

    logger.success(f"ContextOS initialized for '{project_name}'")
    logger.info(f"Goal: {goal}")
    logger.info(f"Location: {contextos_dir}")


# --- Status ---

def cmd_status():
    project_root = find_project_root()
    if not project_root:
        logger.error("No ContextOS project found. Run 'context init' first.")
        return

    engine = Engine(project_root)
    validator = Validator()
    model = engine.load_context()
    status = engine.get_status()
    score = validator.context_score(model)

    # Header panel
    console.print(Panel(
        f"[bold cyan]{status['project']}[/bold cyan]\n"
        f"[white]{status['goal']}[/white]",
        title="ContextOS Status",
        border_style="cyan"
    ))

    # Stats table
    table = Table(box=box.SIMPLE)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Phase", status["phase"])
    table.add_row("Current Task", status["current_task"])
    table.add_row("Current Subtask", status["current_subtask"])
    table.add_row("Progress", status["progress"])
    table.add_row("Context Score", f"{score}/100")

    console.print(table)

    # Tasks table
    task_table = Table(
        title="Tasks",
        box=box.SIMPLE
    )
    task_table.add_column("ID", style="cyan", width=6)
    task_table.add_column("Title", style="white")
    task_table.add_column("Status", style="white")
    task_table.add_column("Priority", style="white")

    for task in status["tasks"]:
        task_table.add_row(
            task.id,
            task.title,
            f"[{status_color(task.status)}]{task.status}[/]",
            f"[{priority_color(task.priority)}]{task.priority}[/]"
        )
        for sub in task.subtasks:
            task_table.add_row(
                f"  {sub.id}",
                f"  {sub.title}",
                f"[{status_color(sub.status)}]{sub.status}[/]",
                f"[{priority_color(sub.priority)}]{sub.priority}[/]"
            )

    console.print(task_table)


# --- Next ---

def cmd_next():
    project_root = find_project_root()
    if not project_root:
        logger.error("No ContextOS project found. Run 'context init' first.")
        return

    engine = Engine(project_root)

    # First check current task subtasks
    current_task = engine.get_current_task()

    if not current_task:
        # No current task — find next pending task
        task = engine.get_next_task()
        if not task:
            logger.success("All tasks completed.")
            return
        engine.set_current_task(task.id)
        current_task = task

    # Find next pending subtask
    subtask = engine.get_next_subtask()

    if subtask:
        engine.set_current_subtask(subtask.id)
        console.print(Panel(
            f"[bold cyan]Current Task:[/bold cyan] {current_task.title}\n"
            f"[bold cyan]Next Subtask:[/bold cyan] {subtask.title}",
            title="Next Up",
            border_style="cyan"
        ))
        logger.info(f"Current subtask set to: {subtask.id}")
    else:
        # All subtasks done — find next pending task
        task = engine.get_next_task()
        if not task:
            logger.success("All tasks completed.")
            return
        engine.set_current_task(task.id)
        console.print(Panel(
            f"[bold cyan]Next Task:[/bold cyan] {task.title}\n"
            f"[bold cyan]Subtasks:[/bold cyan] Run 'context decompose {task.id}' to break it down",
            title="Next Up",
            border_style="cyan"
        ))

# --- Done ---

def cmd_done(task_id: str, dry_run: bool = False):
    project_root = find_project_root()
    if not project_root:
        logger.error("No ContextOS project found. Run 'context init' first.")
        return

    engine = Engine(project_root)
    memory = Memory(get_contextos_dir(project_root))

    if dry_run:
        logger.info(
            f"[DRY RUN] Would mark task {task_id} as done"
        )
        return

    # Snapshot before marking done
    memory.take_snapshot(
        engine.parser.load_raw(),
        label=f"before_done_{task_id}"
    )

    success = engine.update_task_status(task_id, "done")

    if success:
        logger.success(f"Task {task_id} marked as done")
    else:
        logger.error(f"Task {task_id} not found")


# --- Goal ---

def cmd_goal(goal: str):
    project_root = find_project_root()
    if not project_root:
        logger.error("No ContextOS project found. Run 'context init' first.")
        return

    engine = Engine(project_root)
    model = engine.load_context()
    model.project.goal = goal
    engine._context = model
    engine.save_context()
    logger.success(f"Goal updated: {goal}")


# --- Decompose ---

def cmd_decompose(task_id: str, dry_run: bool = False):
    project_root = find_project_root()
    if not project_root:
        logger.error("No ContextOS project found. Run 'context init' first.")
        return

    engine = Engine(project_root)
    model = engine.load_context()
    decomposer = Decomposer()

    task = None
    for t in model.tasks:
        if t.id == task_id:
            task = t
            break

    if not task:
        logger.error(f"Task {task_id} not found")
        return

    suggestions = decomposer.suggest_subtasks(task.title)

    if dry_run:
        logger.info(f"[DRY RUN] Would decompose task {task_id} into:")
        for i, s in enumerate(suggestions):
            console.print(f"  {task_id}.{i+1} — {s}")
        return

    task = decomposer.decompose(task, suggestions)

    for t in model.tasks:
        if t.id == task_id:
            t.subtasks = task.subtasks
            break

    engine._context = model
    engine.save_context()
    logger.success(f"Task {task_id} decomposed into {len(task.subtasks)} subtasks")

    for sub in task.subtasks:
        console.print(f"  [cyan]{sub.id}[/cyan] — {sub.title}")


# --- Suggest ---

def cmd_suggest(task_id: str):
    project_root = find_project_root()
    if not project_root:
        logger.error("No ContextOS project found. Run 'context init' first.")
        return

    engine = Engine(project_root)
    model = engine.load_context()
    suggester = Suggester()
    memory = Memory(get_contextos_dir(project_root))

    task = None
    for t in model.tasks:
        if t.id == task_id:
            task = t
            break

    if not task:
        logger.error(f"Task {task_id} not found")
        return

    suggestions = suggester.suggest(task.title, model)
    formatted = suggester.format_suggestions(suggestions)
    console.print(formatted)

    choice = click.prompt(
        "Select approach",
        type=click.Choice(["A", "B", "C"], case_sensitive=False)
    )

    selection = suggester.record_selection(task_id, choice)
    memory.add_decision(
        task_id=task_id,
        selected_option=choice.upper(),
        rationale="user selected"
    )
    logger.success(f"Decision recorded: [{choice.upper()}] for task {task_id}")


# --- Explain ---

def cmd_explain(task_id: str = None):
    project_root = find_project_root()
    if not project_root:
        logger.error("No ContextOS project found. Run 'context init' first.")
        return

    gateway = Gateway(project_root)
    explanation = gateway.explain(task_id)
    console.print(explanation)


# --- Snapshot ---

def cmd_snapshot(label: str = ""):
    project_root = find_project_root()
    if not project_root:
        logger.error("No ContextOS project found. Run 'context init' first.")
        return

    engine = Engine(project_root)
    memory = Memory(get_contextos_dir(project_root))
    snapshot_id = memory.take_snapshot(
        engine.parser.load_raw(),
        label=label
    )
    logger.success(f"Snapshot saved: {snapshot_id}")


# --- Rollback ---

def cmd_rollback():
    project_root = find_project_root()
    if not project_root:
        logger.error("No ContextOS project found. Run 'context init' first.")
        return

    memory = Memory(get_contextos_dir(project_root))
    snapshots = memory.get_snapshots()

    if not snapshots:
        logger.error("No snapshots found")
        return

    latest = snapshots[-1]
    aicf_data = memory.restore_snapshot(latest["id"])

    if not aicf_data:
        logger.error("Could not restore snapshot")
        return

    write_json(
        get_aicf_path(project_root),
        aicf_data
    )
    logger.success(f"Rolled back to snapshot: {latest['id']}")


# --- Import ---

def cmd_import():
    project_root = find_project_root() or Path.cwd()
    contextos_dir = setup_contextos_dir(project_root)
    aicf_path = contextos_dir / "aicf.json"

    template_path = (
        Path(__file__).parent.parent /
        "templates" /
        "default_context.json"
    )
    aicf_data = read_json(template_path)

    imported = []

    # Import from README.md
    readme = project_root / "README.md"
    if readme.exists():
        with open(readme, "r") as f:
            lines = f.readlines()
        if lines:
            first_line = lines[0].strip().lstrip("#").strip()
            aicf_data["project"]["name"] = first_line
            imported.append("README.md → project name")
        for line in lines:
            if line.lower().startswith("##") and "goal" in line.lower():
                idx = lines.index(line)
                if idx + 1 < len(lines):
                    aicf_data["project"]["goal"] = (
                        lines[idx + 1].strip()
                    )
                    imported.append("README.md → project goal")

    # Import from TODO.md
    todo = project_root / "TODO.md"
    if todo.exists():
        with open(todo, "r") as f:
            lines = f.readlines()
        tasks = []
        task_id = 1
        for line in lines:
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                tasks.append({
                    "id": str(task_id),
                    "title": line[2:].strip(),
                    "status": "pending",
                    "priority": "medium",
                    "subtasks": []
                })
                task_id += 1
        if tasks:
            aicf_data["tasks"] = tasks
            imported.append(f"TODO.md → {len(tasks)} tasks")

    write_json(aicf_path, aicf_data)

    if imported:
        logger.success("Import complete:")
        for item in imported:
            console.print(f"  [cyan]✓[/cyan] {item}")
    else:
        logger.warning("No importable files found")