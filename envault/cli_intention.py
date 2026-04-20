"""CLI commands for managing key intentions."""

import click

from .intention import IntentionError, set_intention, get_intention, remove_intention, list_intentions


@click.group("intention")
def intention_group() -> None:
    """Manage intended purposes for secret keys."""


@intention_group.command("set")
@click.argument("vault_path")
@click.argument("key")
@click.argument("purpose")
@click.option("--owner", default="", help="Owner or team responsible for this key.")
@click.option("--note", default="", help="Additional context or notes.")
def set_cmd(vault_path: str, key: str, purpose: str, owner: str, note: str) -> None:
    """Set the intended PURPOSE for KEY."""
    try:
        entry = set_intention(vault_path, key, purpose, owner or None, note or None)
        click.echo(f"Intention set for '{entry['key']}': {entry['purpose']}")
    except IntentionError as exc:
        raise click.ClickException(str(exc)) from exc


@intention_group.command("get")
@click.argument("vault_path")
@click.argument("key")
def get_cmd(vault_path: str, key: str) -> None:
    """Show the intention for KEY."""
    entry = get_intention(vault_path, key)
    if entry is None:
        click.echo(f"No intention recorded for '{key}'.")
        return
    click.echo(f"Key:     {entry['key']}")
    click.echo(f"Purpose: {entry['purpose']}")
    if entry.get("owner"):
        click.echo(f"Owner:   {entry['owner']}")
    if entry.get("note"):
        click.echo(f"Note:    {entry['note']}")


@intention_group.command("remove")
@click.argument("vault_path")
@click.argument("key")
def remove_cmd(vault_path: str, key: str) -> None:
    """Remove the intention for KEY."""
    removed = remove_intention(vault_path, key)
    if removed:
        click.echo(f"Intention for '{key}' removed.")
    else:
        click.echo(f"No intention found for '{key}'.")


@intention_group.command("list")
@click.argument("vault_path")
def list_cmd(vault_path: str) -> None:
    """List all recorded intentions."""
    entries = list_intentions(vault_path)
    if not entries:
        click.echo("No intentions recorded.")
        return
    for key, entry in sorted(entries.items()):
        owner_part = f" [{entry['owner']}]" if entry.get("owner") else ""
        click.echo(f"{key}{owner_part}: {entry['purpose']}")
