"""CLI commands for vault quota management."""

import click

from envault.cli import get_vault
from envault.quota import (
    QuotaError,
    set_quota,
    get_quota,
    remove_quota,
    check_quota,
)


@click.group("quota")
def quota_group():
    """Manage secret count quotas for a vault."""


@quota_group.command("set")
@click.option("--vault", "vault_path", required=True, help="Path to vault file.")
@click.option("--max", "max_secrets", required=True, type=int, help="Maximum number of secrets.")
def set_cmd(vault_path: str, max_secrets: int):
    """Set the maximum number of secrets allowed in the vault."""
    try:
        result = set_quota(vault_path, max_secrets)
        click.echo(f"Quota set: max_secrets={result['max_secrets']}")
    except QuotaError as exc:
        raise click.ClickException(str(exc))


@quota_group.command("get")
@click.option("--vault", "vault_path", required=True, help="Path to vault file.")
def get_cmd(vault_path: str):
    """Show the current quota for the vault."""
    value = get_quota(vault_path)
    if value is None:
        click.echo("No quota configured.")
    else:
        click.echo(f"max_secrets: {value}")


@quota_group.command("remove")
@click.option("--vault", "vault_path", required=True, help="Path to vault file.")
def remove_cmd(vault_path: str):
    """Remove the quota limit from the vault."""
    removed = remove_quota(vault_path)
    if removed:
        click.echo("Quota removed.")
    else:
        click.echo("No quota was set.")


@quota_group.command("check")
@click.option("--vault", "vault_path", required=True, help="Path to vault file.")
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def check_cmd(vault_path: str, password: str):
    """Check current secret count against the quota."""
    result = check_quota(vault_path, password)
    click.echo(f"Current secrets : {result['current']}")
    if result["max_secrets"] is None:
        click.echo("Quota          : not set")
    else:
        click.echo(f"Quota          : {result['max_secrets']}")
        click.echo(f"Remaining      : {result['remaining']}")
        status = "EXCEEDED" if result["exceeded"] else "OK"
        click.echo(f"Status         : {status}")
