"""CLI commands for vault sync operations."""

import click

from envault.cli import cli, get_vault
from envault.sync import push, pull, status, SyncError


@cli.group("sync")
def sync_group():
    """Sync vault with a remote location."""


@sync_group.command("push")
@click.argument("remote")
@click.option("--vault", "vault_path", default=".envault", show_default=True,
              help="Path to local vault file.")
@click.option("--password", prompt=True, hide_input=True,
              help="Vault password.")
def push_cmd(remote: str, vault_path: str, password: str):
    """Push local vault to REMOTE path."""
    vault = get_vault(vault_path, password)
    try:
        count = push(vault, remote)
        click.echo(f"Pushed {count} key(s) to {remote}")
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


@sync_group.command("pull")
@click.argument("remote")
@click.option("--vault", "vault_path", default=".envault", show_default=True,
              help="Path to local vault file.")
@click.option("--password", prompt=True, hide_input=True,
              help="Vault password.")
@click.option("--overwrite", is_flag=True, default=False,
              help="Overwrite existing local keys.")
def pull_cmd(remote: str, vault_path: str, password: str, overwrite: bool):
    """Pull keys from REMOTE path into local vault."""
    vault = get_vault(vault_path, password)
    try:
        count = pull(vault, remote, overwrite=overwrite)
        click.echo(f"Imported {count} key(s) from {remote}")
    except SyncError as exc:
        raise click.ClickException(str(exc)) from exc


@sync_group.command("status")
@click.argument("remote")
@click.option("--vault", "vault_path", default=".envault", show_default=True,
              help="Path to local vault file.")
@click.option("--password", prompt=True, hide_input=True,
              help="Vault password.")
def status_cmd(remote: str, vault_path: str, password: str):
    """Show diff between local vault and REMOTE."""
    vault = get_vault(vault_path, password)
    result = status(vault, remote)

    if result["only_local"]:
        click.echo("Only local:")
        for k in result["only_local"]:
            click.echo(f"  + {k}")

    if result["only_remote"]:
        click.echo("Only remote:")
        for k in result["only_remote"]:
            click.echo(f"  - {k}")

    if result["common"]:
        click.echo("In sync:")
        for k in result["common"]:
            click.echo(f"    {k}")

    if not any(result.values()):
        click.echo("Vault and remote are identical (both empty).")
