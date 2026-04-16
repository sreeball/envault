"""CLI commands for key access frequency tracking."""

import click
from envault.cli import get_vault
from envault import frequency as freq


@click.group("frequency")
def frequency_group():
    """Track and inspect key access frequency."""


@frequency_group.command("record")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def record_cmd(key, vault_path):
    """Record an access event for KEY."""
    entry = freq.record_access(vault_path, key)
    click.echo(f"Recorded access for {key!r}. Total count: {entry['count']}")


@frequency_group.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def get_cmd(key, vault_path):
    """Show frequency stats for KEY."""
    try:
        entry = freq.get_frequency(vault_path, key)
    except freq.FrequencyError as e:
        raise click.ClickException(str(e))
    click.echo(f"Key:            {key}")
    click.echo(f"Access count:   {entry['count']}")
    click.echo(f"First accessed: {entry['first_accessed']}")
    click.echo(f"Last accessed:  {entry['last_accessed']}")


@frequency_group.command("reset")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def reset_cmd(key, vault_path):
    """Reset frequency data for KEY."""
    freq.reset_frequency(vault_path, key)
    click.echo(f"Frequency data reset for {key!r}.")


@frequency_group.command("list")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
@click.option("--top", default=0, help="Limit to top N keys by access count.")
def list_cmd(vault_path, top):
    """List keys sorted by access frequency."""
    entries = freq.list_frequency(vault_path, top=top)
    if not entries:
        click.echo("No frequency data recorded.")
        return
    for e in entries:
        click.echo(f"{e['key']}: {e['count']} access(es), last: {e['last_accessed']}")
