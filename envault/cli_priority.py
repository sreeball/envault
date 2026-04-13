"""CLI commands for key priority management."""
import click

from .priority import (
    PriorityError,
    set_priority,
    get_priority,
    remove_priority,
    list_by_priority,
    VALID_LEVELS,
)


@click.group("priority")
def priority_group():
    """Manage key priorities."""


@priority_group.command("set")
@click.argument("key")
@click.argument("level", type=click.Choice(VALID_LEVELS))
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
def set_cmd(key, level, vault):
    """Assign a LEVEL priority to KEY."""
    try:
        result = set_priority(vault, key, level)
        click.echo(f"Set priority for '{result['key']}' to '{result['priority']}'.")
    except PriorityError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@priority_group.command("get")
@click.argument("key")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
def get_cmd(key, vault):
    """Show the priority level for KEY."""
    level = get_priority(vault, key)
    if level is None:
        click.echo(f"No priority set for '{key}'.")
    else:
        click.echo(f"{key}: {level}")


@priority_group.command("remove")
@click.argument("key")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
def remove_cmd(key, vault):
    """Remove the priority entry for KEY."""
    try:
        remove_priority(vault, key)
        click.echo(f"Removed priority for '{key}'.")
    except PriorityError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@priority_group.command("list")
@click.option("--vault", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
@click.option("--level", type=click.Choice(VALID_LEVELS), default=None, help="Filter by level.")
def list_cmd(vault, level):
    """List keys and their priorities."""
    try:
        entries = list_by_priority(vault, level=level)
    except PriorityError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    if not entries:
        click.echo("No priorities set.")
        return
    for entry in entries:
        click.echo(f"{entry['key']}: {entry['priority']}")
