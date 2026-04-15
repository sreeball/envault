"""CLI commands for secret ownership management."""
import click
from envault.cli import get_vault
from envault.ownership import (
    OwnershipError,
    set_owner,
    get_owner,
    remove_owner,
    list_owned_by,
    list_all,
)


@click.group("ownership")
def ownership_group():
    """Manage secret ownership."""


@ownership_group.command("set")
@click.argument("key")
@click.argument("owner")
@click.option("--team", default=None, help="Team responsible for this secret.")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True)
def set_cmd(key, owner, team, vault_path):
    """Assign an owner to a secret KEY."""
    try:
        entry = set_owner(vault_path, key, owner, team=team)
        click.echo(f"Owner set: {entry['owner']}" + (f" (team: {entry['team']})" if entry["team"] else ""))
    except OwnershipError as exc:
        raise click.ClickException(str(exc))


@ownership_group.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True)
def get_cmd(key, vault_path):
    """Show ownership info for a secret KEY."""
    try:
        entry = get_owner(vault_path, key)
        click.echo(f"owner: {entry['owner']}")
        click.echo(f"team:  {entry['team'] or '(none)'}")
    except OwnershipError as exc:
        raise click.ClickException(str(exc))


@ownership_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True)
def remove_cmd(key, vault_path):
    """Remove ownership record for KEY."""
    try:
        remove_owner(vault_path, key)
        click.echo(f"Ownership record removed for '{key}'.")
    except OwnershipError as exc:
        raise click.ClickException(str(exc))


@ownership_group.command("list")
@click.option("--owner", default=None, help="Filter by owner name.")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True)
def list_cmd(owner, vault_path):
    """List ownership records, optionally filtered by owner."""
    if owner:
        keys = list_owned_by(vault_path, owner)
        if not keys:
            click.echo(f"No keys owned by '{owner}'.")
        else:
            for k in sorted(keys):
                click.echo(k)
    else:
        data = list_all(vault_path)
        if not data:
            click.echo("No ownership records found.")
        else:
            for k, v in sorted(data.items()):
                team_str = f"  team={v['team']}" if v["team"] else ""
                click.echo(f"{k}: {v['owner']}{team_str}")
