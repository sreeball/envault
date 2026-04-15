"""CLI commands for managing secret metadata."""

import click

from envault.cli import get_vault
from envault.metadata import MetadataError, get_meta, keys_with_field, list_meta, remove_meta, set_meta


@click.group("metadata")
def metadata_group() -> None:
    """Attach and query metadata fields on secrets."""


@metadata_group.command("set")
@click.argument("key")
@click.argument("field")
@click.argument("value")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def set_cmd(key: str, field: str, value: str, vault_path: str) -> None:
    """Set FIELD=VALUE on KEY's metadata."""
    try:
        result = set_meta(vault_path, key, field, value)
        click.echo(f"Set '{field}' on '{key}'.")
        for f, v in result.items():
            click.echo(f"  {f}: {v}")
    except MetadataError as exc:
        raise click.ClickException(str(exc)) from exc


@metadata_group.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def get_cmd(key: str, vault_path: str) -> None:
    """Print all metadata fields for KEY."""
    meta = get_meta(vault_path, key)
    if not meta:
        click.echo(f"No metadata for '{key}'.")
        return
    for field, value in meta.items():
        click.echo(f"{field}: {value}")


@metadata_group.command("remove")
@click.argument("key")
@click.argument("field")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def remove_cmd(key: str, field: str, vault_path: str) -> None:
    """Remove FIELD from KEY's metadata."""
    try:
        remove_meta(vault_path, key, field)
        click.echo(f"Removed '{field}' from '{key}'.")
    except MetadataError as exc:
        raise click.ClickException(str(exc)) from exc


@metadata_group.command("list")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def list_cmd(vault_path: str) -> None:
    """List all metadata across all keys."""
    all_meta = list_meta(vault_path)
    if not all_meta:
        click.echo("No metadata stored.")
        return
    for key, fields in all_meta.items():
        click.echo(f"[{key}]")
        for field, value in fields.items():
            click.echo(f"  {field}: {value}")


@metadata_group.command("find")
@click.argument("field")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def find_cmd(field: str, vault_path: str) -> None:
    """Find all keys that have FIELD set."""
    keys = keys_with_field(vault_path, field)
    if not keys:
        click.echo(f"No keys have field '{field}'.")
        return
    for k in keys:
        click.echo(k)
