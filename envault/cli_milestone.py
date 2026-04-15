"""CLI commands for milestone management."""
import click
from envault.cli import get_vault
from envault.milestone import (
    MilestoneError,
    create_milestone,
    complete_milestone,
    delete_milestone,
    list_milestones,
)


@click.group("milestone")
def milestone_group():
    """Manage project milestones."""


@milestone_group.command("create")
@click.argument("name")
@click.option("-d", "--description", default="", help="Milestone description.")
@click.option("--due", default=None, help="Due date as ISO string.")
@click.option("-v", "--vault", default="vault.db", show_default=True)
def create_cmd(name, description, due, vault):
    """Create a new milestone."""
    try:
        entry = create_milestone(vault, name, description=description, due_date=due)
        click.echo(f"Milestone '{entry['name']}' created (id={entry['id']}).")
    except MilestoneError as exc:
        raise click.ClickException(str(exc))


@milestone_group.command("complete")
@click.argument("name")
@click.option("-v", "--vault", default="vault.db", show_default=True)
def complete_cmd(name, vault):
    """Mark a milestone as completed."""
    try:
        entry = complete_milestone(vault, name)
        click.echo(f"Milestone '{name}' completed at {entry['completed_at']}.")
    except MilestoneError as exc:
        raise click.ClickException(str(exc))


@milestone_group.command("delete")
@click.argument("name")
@click.option("-v", "--vault", default="vault.db", show_default=True)
def delete_cmd(name, vault):
    """Delete a milestone."""
    try:
        delete_milestone(vault, name)
        click.echo(f"Milestone '{name}' deleted.")
    except MilestoneError as exc:
        raise click.ClickException(str(exc))


@milestone_group.command("list")
@click.option("-v", "--vault", default="vault.db", show_default=True)
def list_cmd(vault):
    """List all milestones."""
    milestones = list_milestones(vault)
    if not milestones:
        click.echo("No milestones found.")
        return
    for m in milestones:
        status = "done" if m["completed_at"] else "open"
        due = m["due_date"] or "—"
        click.echo(f"[{status}] {m['name']}  due={due}  {m['description']}")
