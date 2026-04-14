"""CLI commands for managing delegations."""

from __future__ import annotations

import json

import click

from envault.cli import get_vault
from envault.delegation import (
    DelegationError,
    create_delegation,
    revoke_delegation,
    check_delegation,
    list_delegations,
)


@click.group("delegation")
def delegation_group() -> None:
    """Manage scoped, time-limited delegations."""


@delegation_group.command("create")
@click.option("--vault", "vault_path", required=True, help="Path to vault file.")
@click.option("--password", prompt=True, hide_input=True)
@click.argument("delegatee")
@click.argument("keys", nargs=-1, required=True)
@click.option("--ttl", default=3600, show_default=True, help="TTL in seconds.")
@click.option("--note", default="", help="Optional note.")
def create_cmd(
    vault_path: str,
    password: str,
    delegatee: str,
    keys: tuple,
    ttl: int,
    note: str,
) -> None:
    """Create a delegation token for DELEGATEE granting access to KEYS."""
    try:
        entry = create_delegation(vault_path, delegatee, list(keys), ttl, note)
        click.echo(f"Token : {entry['token']}")
        click.echo(f"Expires: {entry['expires_at']}")
    except DelegationError as exc:
        raise click.ClickException(str(exc)) from exc


@delegation_group.command("revoke")
@click.option("--vault", "vault_path", required=True)
@click.argument("token")
def revoke_cmd(vault_path: str, token: str) -> None:
    """Revoke a delegation TOKEN."""
    try:
        revoke_delegation(vault_path, token)
        click.echo(f"Revoked {token}")
    except DelegationError as exc:
        raise click.ClickException(str(exc)) from exc


@delegation_group.command("check")
@click.option("--vault", "vault_path", required=True)
@click.argument("token")
@click.argument("key")
def check_cmd(vault_path: str, token: str, key: str) -> None:
    """Check whether TOKEN grants access to KEY."""
    if check_delegation(vault_path, token, key):
        click.echo("allowed")
    else:
        click.echo("denied")
        raise SystemExit(1)


@delegation_group.command("list")
@click.option("--vault", "vault_path", required=True)
def list_cmd(vault_path: str) -> None:
    """List all delegations."""
    entries = list_delegations(vault_path)
    if not entries:
        click.echo("No delegations found.")
        return
    for e in entries:
        click.echo(
            f"{e['token']}  delegatee={e['delegatee']}  "
            f"keys={','.join(e['keys'])}  expires={e['expires_at']}"
        )
