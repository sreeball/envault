"""CLI commands for scope management."""

from __future__ import annotations

import click

from envault.cli import get_vault
from envault.scope import (
    ScopeError,
    add_to_scope,
    delete_scope,
    keys_in_scope,
    list_scopes,
    remove_from_scope,
)


@click.group("scope")
def scope_group() -> None:
    """Manage key scopes."""


@scope_group.command("add")
@click.argument("scope")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def add_cmd(scope: str, key: str, vault_path: str) -> None:
    """Add KEY to SCOPE."""
    try:
        result = add_to_scope(vault_path, scope, key)
        click.echo(f"Added '{key}' to scope '{scope}'. Keys: {', '.join(result['keys'])}")
    except ScopeError as exc:
        raise click.ClickException(str(exc)) from exc


@scope_group.command("remove")
@click.argument("scope")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def remove_cmd(scope: str, key: str, vault_path: str) -> None:
    """Remove KEY from SCOPE."""
    try:
        remove_from_scope(vault_path, scope, key)
        click.echo(f"Removed '{key}' from scope '{scope}'.")
    except ScopeError as exc:
        raise click.ClickException(str(exc)) from exc


@scope_group.command("keys")
@click.argument("scope")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def keys_cmd(scope: str, vault_path: str) -> None:
    """List all keys in SCOPE."""
    try:
        keys = keys_in_scope(vault_path, scope)
        if keys:
            click.echo("\n".join(keys))
        else:
            click.echo(f"Scope '{scope}' is empty.")
    except ScopeError as exc:
        raise click.ClickException(str(exc)) from exc


@scope_group.command("list")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def list_cmd(vault_path: str) -> None:
    """List all scopes."""
    scopes = list_scopes(vault_path)
    if not scopes:
        click.echo("No scopes defined.")
        return
    for scope, keys in scopes.items():
        click.echo(f"{scope}: {', '.join(keys) if keys else '(empty)'}")


@scope_group.command("delete")
@click.argument("scope")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def delete_cmd(scope: str, vault_path: str) -> None:
    """Delete an entire SCOPE."""
    try:
        delete_scope(vault_path, scope)
        click.echo(f"Scope '{scope}' deleted.")
    except ScopeError as exc:
        raise click. exc
