"""CLI commands for the spotlight feature."""

import click
from envault.cli import get_vault
from envault import spotlight as sp


@click.group("spotlight")
def spotlight_group():
    """Highlight and manage featured secrets."""


@spotlight_group.command("add")
@click.argument("key")
@click.option("--reason", default="", help="Why this key is featured.")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def add_cmd(key, reason, vault_path):
    """Highlight a secret key."""
    entry = sp.highlight(vault_path, key, reason=reason)
    click.echo(f"Highlighted '{entry['key']}'.")
    if reason:
        click.echo(f"Reason: {reason}")


@spotlight_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def remove_cmd(key, vault_path):
    """Remove a key from the spotlight."""
    try:
        sp.remove_highlight(vault_path, key)
        click.echo(f"Removed '{key}' from spotlight.")
    except sp.SpotlightError as exc:
        raise click.ClickException(str(exc))


@spotlight_group.command("list")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def list_cmd(vault_path):
    """List all highlighted keys."""
    data = sp.get_highlighted(vault_path)
    if not data:
        click.echo("No keys are currently highlighted.")
        return
    for key, entry in data.items():
        reason = entry.get("reason") or "-"
        click.echo(f"{key}  (reason: {reason})")


@spotlight_group.command("check")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def check_cmd(key, vault_path):
    """Check if a key is highlighted."""
    if sp.is_highlighted(vault_path, key):
        click.echo(f"'{key}' is highlighted.")
    else:
        click.echo(f"'{key}' is not highlighted.")
