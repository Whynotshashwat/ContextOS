from pathlib import Path

import os
import atexit
import tempfile

import click
from cli.commands import (
    cmd_init,
    cmd_status,
    cmd_next,
    cmd_done,
    cmd_goal,
    cmd_decompose,
    cmd_suggest,
    cmd_explain,
    cmd_snapshot,
    cmd_rollback,
    cmd_import
)

from rich.console import Console
from rich.text import Text

console = Console()


def print_banner():
    """Print ContextOS startup banner — once per terminal session."""
    from utils.helpers import find_project_root
    from core.config import Config

    # Use terminal PID as session identifier
    terminal_pid = os.environ.get("SESSIONNAME", "") + str(os.getpid())
    session_flag = os.path.join(
        tempfile.gettempdir(),
        f"contextos_{terminal_pid}"
    )

    if os.path.exists(session_flag):
        return

    with open(session_flag, "w", encoding="utf-8") as f:
        f.write("shown")

    def _cleanup_flag():
        if os.path.exists(session_flag):
            os.remove(session_flag)

    atexit.register(_cleanup_flag)

    project_root = find_project_root()
    cfg = Config(project_root) if project_root else None

    provider = cfg.get_provider_display() if cfg else "Anthropic"
    model = cfg.get_model_display() if cfg else "claude-sonnet-4-6"
    agent = cfg.get_agent_display() if cfg else "Claude Code"

    banner = """
 ██████╗ ██████╗ ███╗   ██╗████████╗███████╗██╗  ██╗████████╗ ██████╗ ███████╗
██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝╚██╗██╔╝╚══██╔══╝██╔═══██╗██╔════╝
██║     ██║   ██║██╔██╗ ██║   ██║   █████╗   ╚███╔╝    ██║   ██║   ██║███████╗
██║     ██║   ██║██║╚██╗██║   ██║   ██╔══╝   ██╔██╗    ██║   ██║   ██║╚════██║
╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████╗██╔╝ ██╗   ██║   ╚██████╔╝███████║
 ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚══════╝"""

    console.print(f"[bold magenta]{banner}[/bold magenta]")
    console.print(f"[bold white]  v0.3.0  ·  AI Context Infrastructure Layer[/bold white]")
    console.print(f"[dim]  {'─' * 55}[/dim]")
    console.print(f"[cyan]  Agent    :[/cyan] [white]{agent}[/white]")
    console.print(f"[cyan]  Model    :[/cyan] [white]{model}[/white]")
    console.print(f"[cyan]  Provider :[/cyan] [white]{provider}[/white]")
    console.print(f"[dim]  {'─' * 55}[/dim]\n")

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    ContextOS — AI Context Infrastructure Layer
    Reduce token consumption. Maintain AI continuity.
    """
    if ctx.invoked_subcommand is not None:
        print_banner()

# --- Init ---

@cli.command()
@click.argument("project_name")
@click.argument("goal")
def init(project_name, goal):
    """Initialize ContextOS in current project."""
    cmd_init(project_name, goal)


# --- Status ---

@cli.command()
def status():
    """Show current project context and progress."""
    cmd_status()


# --- Next ---

@cli.command()
def next():
    """Show and set the next pending task."""
    cmd_next()


# --- Done ---

@cli.command()
@click.argument("task_id")
@click.option("--dry-run", is_flag=True, default=False)
def done(task_id, dry_run):
    """Mark a task or subtask as done."""
    cmd_done(task_id, dry_run)


# --- Goal ---

@cli.command()
@click.argument("goal")
def goal(goal):
    """Update the project goal."""
    cmd_goal(goal)


# --- Decompose ---

@cli.command()
@click.argument("task_id")
@click.option("--dry-run", is_flag=True, default=False)
def decompose(task_id, dry_run):
    """Break a task into subtasks."""
    cmd_decompose(task_id, dry_run)


# --- Suggest ---

@cli.command()
@click.argument("task_id")
def suggest(task_id):
    """Get A/B/C implementation suggestions for a task."""
    cmd_suggest(task_id)


# --- Explain ---

@cli.command()
@click.argument("task_id", required=False)
def explain(task_id):
    """Show what context would be injected for a task."""
    cmd_explain(task_id)


# --- Snapshot ---

@cli.command()
@click.argument("label", required=False, default="")
def snapshot(label):
    """Save a manual context snapshot."""
    cmd_snapshot(label)


# --- Rollback ---

@cli.command()
def rollback():
    """Restore the last context snapshot."""
    cmd_rollback()


# --- Import ---

@cli.command()
def import_context():
    """Import context from existing project files."""
    cmd_import()


# --- Compress ---

@cli.command()
def compress():
    """Compress context history."""
    from cli.commands import cmd_compress
    cmd_compress()


# --- Log ---

@cli.command()
def log():
    """View recent AI interaction log."""
    from cli.commands import cmd_log
    cmd_log()


# --- Stats ---

@cli.command()
@click.option("--baseline", type=int, default=None,
              help="Your typical raw prompt size in tokens for reduction calculation.")
def stats(baseline):
    """Show context usage statistics."""
    from cli.commands import cmd_stats
    cmd_stats(baseline)


# --- Ignore ---

@cli.group()
def ignore():
    """Manage .contextosignore rules."""
    pass


@ignore.command("init")
def ignore_init():
    """Create default .contextosignore file."""
    from cli.commands import cmd_ignore_init
    cmd_ignore_init()


@ignore.command("list")
def ignore_list():
    """List current ignore rules."""
    from cli.commands import cmd_ignore_list
    cmd_ignore_list()


# --- Config ---

@cli.group(name="config")
def config_group():
    """Manage ContextOS configuration."""
    pass


@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a config value. Keys: provider, model, agent, api_key_env"""
    from utils.helpers import find_project_root
    from core.config import Config
    from core.config import (
        SUPPORTED_PROVIDERS,
        SUPPORTED_MODELS,
        SUPPORTED_AGENTS
    )
    from utils.logger import logger
    project_root = find_project_root() or Path.cwd()
    cfg = Config(project_root)

    supported_keys = ["provider", "model", "agent", "api_key_env"]
    if key not in supported_keys:
        logger.error(f"Unknown config key: {key}. Valid keys: {', '.join(supported_keys)}")
        return

    if key == "provider" and value not in SUPPORTED_PROVIDERS:
        logger.error(f"Invalid provider: {value}. Valid: {', '.join(SUPPORTED_PROVIDERS)}")
        return
    if key == "model" and value not in SUPPORTED_MODELS:
        logger.error(f"Invalid model: {value}. Valid: {', '.join(SUPPORTED_MODELS)}")
        return
    if key == "agent" and value not in SUPPORTED_AGENTS:
        logger.error(f"Invalid agent: {value}. Valid: {', '.join(SUPPORTED_AGENTS)}")
        return

    cfg.set(key, value)
    logger.success(f"Config updated: {key} = {value}")


@config_group.command("show")
def config_show():
    """Show current configuration."""
    from utils.helpers import find_project_root
    from core.config import Config
    from rich.table import Table
    from rich import box
    project_root = find_project_root() or Path.cwd()
    cfg = Config(project_root)
    data = cfg.all()
    table = Table(box=box.SIMPLE)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    for k, v in data.items():
        table.add_row(k, v)
    console.print(table)


# --- Entry Point ---

if __name__ == "__main__":
    cli()