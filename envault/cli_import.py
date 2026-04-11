"""CLI commands for importing environment variables into a vault."""

from __future__ import annotations

import click

from envault.cli import get_vault
from envault.import_env import (
    ImportError as EnvImportError,
    import_from_env,
    import_from_file,
    load_into_vault,
)


@click.group("import")
def import_group() -> None:  # pragma: no cover
    """Import secrets into the vault from various sources."""


@import_group.command("file")
@click.argument("source", type=click.Path(exists=True, dir_okay=False))
@click.option("--fmt", default="dotenv", show_default=True,
              type=click.Choice(["dotenv", "json"]),
              help="Format of the source file.")
@click.option("--vault", "vault_path", default="vault.json", show_default=True,
              help="Path to the vault file.")
@click.password_option("--password", prompt="Vault password",
                       confirmation_prompt=False)
def import_file_cmd(source: str, fmt: str, vault_path: str, password: str) -> None:
    """Import secrets from a .env or JSON file into the vault."""
    try:
        secrets = import_from_file(source, fmt=fmt)
    except EnvImportError as exc:
        raise click.ClickException(str(exc)) from exc

    vault = get_vault(vault_path)
    try:
        added, updated = load_into_vault(vault, secrets, password)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Imported {len(secrets)} secret(s): {added} added, {updated} updated.")


@import_group.command("env")
@click.argument("keys", nargs=-1)
@click.option("--vault", "vault_path", default="vault.json", show_default=True,
              help="Path to the vault file.")
@click.password_option("--password", prompt="Vault password",
                       confirmation_prompt=False)
def import_env_cmd(keys: tuple[str, ...], vault_path: str, password: str) -> None:
    """Import secrets from the current environment.

    Optionally pass explicit KEY names; omit to capture all variables.
    """
    key_list = list(keys) if keys else None
    try:
        secrets = import_from_env(key_list)
    except EnvImportError as exc:
        raise click.ClickException(str(exc)) from exc

    vault = get_vault(vault_path)
    try:
        added, updated = load_into_vault(vault, secrets, password)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Imported {len(secrets)} secret(s): {added} added, {updated} updated.")
