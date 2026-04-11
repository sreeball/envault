"""CLI commands for key aliasing."""

from __future__ import annotations

import click

from envault.alias import AliasError, add_alias, remove_alias, resolve, list_aliases
from envault.cli import get_vault


@click.group("alias", help="Manage short-name aliases for secret keys.")
def alias_group() -> None:
    pass


@alias_group.command("add")
@click.argument("alias")
@click.argument("key")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True, help="Path to vault file.")
def add_cmd(alias: str, key: str, vault_path: str) -> None:
    """Add ALIAS as a short name for KEY."""
    try:
        entry = add_alias(vault_path, alias, key)
        click.echo(f"Alias '{entry['alias']}' → '{entry['key']}' added.")
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc


@alias_group.command("remove")
@click.argument("alias")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True, help="Path to vault file.")
def remove_cmd(alias: str, vault_path: str) -> None:
    """Remove an alias."""
    try:
        entry = remove_alias(vault_path(f"Alias '{entry['alias']}' removed.")
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc


@alias_group.command("resolve")
@click.argument("name")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True, help="Path to vault file.")
def resolve_cmd(name: str, vault_path: str) -> None:
    """Print the canonical key that NAME resolves to."""
    click.echo(resolve(vault_path, name))


@alias_group.command("list")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True, help="Path to vault file.")
def list_cmd(vault_path: str) -> None:
    """List all registered aliases."""
    entries = list_aliases(vault_path)
    if not entries:
        click.echo("No aliases defined.")
        return
    for e in entries:
        click.echo(f"{e['alias']:30s} → {e['key']}")
