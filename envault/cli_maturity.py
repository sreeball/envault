"""CLI commands for maturity management."""
import click
from envault.maturity import (
    set_maturity, get_maturity, remove_maturity, list_maturity,
    keys_at_level, MaturityError, MATURITY_LEVELS
)


@click.group("maturity")
def maturity_group():
    """Manage maturity levels for secrets."""


@maturity_group.command("set")
@click.argument("vault_path")
@click.argument("key")
@click.argument("level", type=click.Choice(MATURITY_LEVELS))
@click.option("--note", default="", help="Optional note about the maturity level.")
def set_cmd(vault_path, key, level, note):
    """Set the maturity level for a secret KEY."""
    try:
        entry = set_maturity(vault_path, key, level, note=note)
        click.echo(f"Set maturity for '{key}': {entry['level']}")
    except MaturityError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@maturity_group.command("get")
@click.argument("vault_path")
@click.argument("key")
def get_cmd(vault_path, key):
    """Get the maturity level for a secret KEY."""
    entry = get_maturity(vault_path, key)
    if entry is None:
        click.echo(f"No maturity set for '{key}'.")
    else:
        note_part = f" ({entry['note']})" if entry["note"] else ""
        click.echo(f"{key}: {entry['level']}{note_part}")


@maturity_group.command("remove")
@click.argument("vault_path")
@click.argument("key")
def remove_cmd(vault_path, key):
    """Remove maturity entry for a secret KEY."""
    removed = remove_maturity(vault_path, key)
    if removed:
        click.echo(f"Removed maturity for '{key}'.")
    else:
        click.echo(f"No maturity entry found for '{key}'.")


@maturity_group.command("list")
@click.argument("vault_path")
@click.option("--level", type=click.Choice(MATURITY_LEVELS), default=None, help="Filter by level.")
def list_cmd(vault_path, level):
    """List all maturity entries, optionally filtered by LEVEL."""
    if level:
        keys = keys_at_level(vault_path, level)
        if not keys:
            click.echo(f"No keys at level '{level}'.")
        else:
            for k in keys:
                click.echo(k)
    else:
        data = list_maturity(vault_path)
        if not data:
            click.echo("No maturity entries found.")
        else:
            for k, v in data.items():
                note_part = f" — {v['note']}" if v["note"] else ""
                click.echo(f"{k}: {v['level']}{note_part}")
