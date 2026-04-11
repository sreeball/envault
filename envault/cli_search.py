"""CLI commands for searching secrets inside a vault."""

from __future__ import annotations

import json

import click

from envault.cli import get_vault
from envault.search import SearchError, list_keys_matching, search


@click.group("search")
def search_group() -> None:
    """Search and filter secrets in the vault."""


@search_group.command("keys")
@click.argument("pattern")
@click.option("--regex", is_flag=True, help="Treat PATTERN as a regular expression.")
@click.option("--vault", "vault_path", default="vault.json", show_default=True)
def keys_cmd(pattern: str, regex: bool, vault_path: str) -> None:
    """List keys matching PATTERN (no decryption needed)."""
    v = get_vault(vault_path)
    try:
        keys = list_keys_matching(v, pattern, regex=regex)
    except SearchError as exc:
        raise click.ClickException(str(exc)) from exc

    if not keys:
        click.echo("No matching keys found.")
        return
    for key in keys:
        click.echo(key)


@search_group.command("secrets")
@click.argument("pattern")
@click.password_option(prompt="Master password", confirmation_prompt=False)
@click.option("--regex", is_flag=True, help="Treat PATTERN as a regular expression.")
@click.option("--keys-only", is_flag=True, help="Only match against keys.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "keys"]),
    default="table",
    show_default=True,
)
@click.option("--vault", "vault_path", default="vault.json", show_default=True)
def secrets_cmd(
    pattern: str,
    password: str,
    regex: bool,
    keys_only: bool,
    fmt: str,
    vault_path: str,
) -> None:
    """Search secrets matching PATTERN."""
    v = get_vault(vault_path)
    try:
        results = search(v, password, pattern, regex=regex, keys_only=keys_only)
    except SearchError as exc:
        raise click.ClickException(str(exc)) from exc

    if not results:
        click.echo("No matching secrets found.")
        return

    if fmt == "json":
        click.echo(json.dumps(results, indent=2))
    elif fmt == "keys":
        for key in results:
            click.echo(key)
    else:
        max_key_len = max(len(k) for k in results)
        for key, value in results.items():
            click.echo(f"{key:<{max_key_len}}  {value}")
