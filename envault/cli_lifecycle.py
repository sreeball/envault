"""CLI commands for lifecycle state management."""

import click
from envault.cli import get_vault
from envault import lifecycle


@click.group("lifecycle")
def lifecycle_group():
    """Manage the lifecycle state of secrets."""


@lifecycle_group.command("set")
@click.argument("key")
@click.argument("state", type=click.Choice(lifecycle.VALID_STATES))
@click.option("--note", default="", help="Optional note about the state change.")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def set_cmd(key, state, note, vault_path):
    """Set the lifecycle STATE of KEY."""
    try:
        entry = lifecycle.set_state(vault_path, key, state, note or None)
        click.echo(f"[{key}] state → {entry['state']}")
        if entry["note"]:
            click.echo(f"  note: {entry['note']}")
    except lifecycle.LifecycleError as exc:
        raise click.ClickException(str(exc))


@lifecycle_group.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def get_cmd(key, vault_path):
    """Show the lifecycle state of KEY."""
    entry = lifecycle.get_state(vault_path, key)
    click.echo(f"state: {entry['state']}")
    if entry.get("note"):
        click.echo(f"note:  {entry['note']}")


@lifecycle_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def remove_cmd(key, vault_path):
    """Remove lifecycle tracking for KEY."""
    removed = lifecycle.remove_state(vault_path, key)
    if removed:
        click.echo(f"Lifecycle state for '{key}' removed.")
    else:
        click.echo(f"No lifecycle state found for '{key}'.")


@lifecycle_group.command("list")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def list_cmd(vault_path):
    """List all tracked lifecycle states."""
    states = lifecycle.list_states(vault_path)
    if not states:
        click.echo("No lifecycle states tracked.")
        return
    for key, entry in sorted(states.items()):
        note_part = f"  # {entry['note']}" if entry.get("note") else ""
        click.echo(f"{key}: {entry['state']}{note_part}")
