from pathlib import Path

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
    """Print ContextOS startup banner."""
    from utils.helpers import find_project_root
    from core.config import Config

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
    console.print(f"[bold white]  v0.2.0  ·  AI Context Infrastructure Layer[/bold white]")
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
    from utils.logger import logger
    project_root = find_project_root() or Path.cwd()
    cfg = Config(project_root)
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