"""CLI commands for managing access-control on vault keys."""

import click
from envault.cli import get_vault
from envault.access import grant, revoke, can, list_permissions, AccessError


@click.group("access")
def access_group():
    """Manage read/write permissions for identities on vault keys."""


@access_group.command("grant")
@click.argument("identity")
@click.argument("key")
@click.option(
    "--permission", "-p",
    default="read",
    type=click.Choice(["read", "write"]),
    show_default=True,
    help="Permission to grant.",
)
@click.pass_context
def grant_cmd(ctx, identity, key, permission):
    """Grant IDENTITY the given PERMISSION on KEY."""
    vault = get_vault(ctx)
    try:
        grant(vault.path, identity, key, permission)
        click.echo(f"Granted {permission} on '{key}' to '{identity}'.")
    except AccessError as exc:
        raise click.ClickException(str(exc))


@access_group.command("revoke")
@click.argument("identity")
@click.argument("key")
@click.option(
    "--permission", "-p",
    default="read",
    type=click.Choice(["read", "write"]),
    show_default=True,
    help="Permission to revoke.",
)
@click.pass_context
def revoke_cmd(ctx, identity, key, permission):
    """Revoke IDENTITY's PERMISSION on KEY."""
    vault = get_vault(ctx)
    try:
        revoke(vault.path, identity, key, permission)
        click.echo(f"Revoked {permission} on '{key}' from '{identity}'.")
    except AccessError as exc:
        raise click.ClickException(str(exc))


@access_group.command("check")
@click.argument("identity")
@click.argument("key")
@click.option(
    "--permission", "-p",
    default="read",
    type=click.Choice(["read", "write"]),
    show_default=True,
)
@click.pass_context
def check_cmd(ctx, identity, key, permission):
    """Check whether IDENTITY holds PERMISSION on KEY."""
    vault = get_vault(ctx)
    allowed = can(vault.path, identity, key, permission)
    status = "allowed" if allowed else "denied"
    click.echo(f"{identity} -> {key} [{permission}]: {status}")


@access_group.command("list")
@click.argument("identity", required=False, default=None)
@click.pass_context
def list_cmd(ctx, identity):
    """List permissions, optionally filtered to IDENTITY."""
    vault = get_vault(ctx)
    perms = list_permissions(vault.path, identity)
    if not perms:
        click.echo("No access rules defined.")
        return
    for ident, rules in perms.items():
        for perm, keys in rules.items():
            for k in keys:
                click.echo(f"{ident}  {perm}  {k}")
