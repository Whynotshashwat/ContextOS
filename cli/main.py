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


@click.group()
def cli():
    """
    ContextOS — AI Context Infrastructure Layer
    Reduce token consumption. Maintain AI continuity.
    """
    pass


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

# --- Entry Point ---

if __name__ == "__main__":
    cli()