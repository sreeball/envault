"""CLI commands for staleness tracking."""

import click
from envault.cli import get_vault
from envault import staleness as sl


@click.group("staleness")
def staleness_group():
    """Track and report secret staleness."""


@staleness_group.command("record")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def record_cmd(key, vault_path):
    """Record that KEY was just updated."""
    entry = sl.record_update(vault_path, key)
    click.echo(f"Recorded update for '{key}' at {entry['last_updated']}.")


@staleness_group.command("get")
@click.argument("key")
@click.option("--max-age", default=90, show_default=True, help="Max age in days before stale.")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def get_cmd(key, max_age, vault_path):
    """Show staleness info for KEY."""
    info = sl.get_staleness(vault_path, key, max_age_days=max_age)
    if info["last_updated"] is None:
        click.echo(f"No staleness record found for '{key}'.")
        return
    status = "STALE" if info["stale"] else "fresh"
    click.echo(f"{key}: {status} (age {info['age_days']} days, last updated {info['last_updated']})")


@staleness_group.command("list")
@click.option("--max-age", default=90, show_default=True, help="Max age in days before stale.")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def list_cmd(max_age, vault_path):
    """List all stale keys."""
    stale = sl.list_stale(vault_path, max_age_days=max_age)
    if not stale:
        click.echo("No stale keys found.")
        return
    for entry in stale:
        click.echo(f"{entry['key']}: {entry['age_days']} days old (last updated {entry['last_updated']})")


@staleness_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def remove_cmd(key, vault_path):
    """Remove staleness record for KEY."""
    removed = sl.remove_record(vault_path, key)
    if removed:
        click.echo(f"Removed staleness record for '{key}'.")
    else:
        click.echo(f"No record found for '{key}'.")
