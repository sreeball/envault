"""Command-line interface for envault."""

import sys
from pathlib import Path

import click

from envault.vault import Vault
from envault.export import export_secrets, ExportFormat

DEFAULT_VAULT = ".envault"


def get_vault(vault_path: str, password: str) -> Vault:
    return Vault(path=vault_path, password=password)


@click.group()
def cli() -> None:
    """envault — securely manage environment variables."""


@cli.command("set")
@click.option("--vault", default=DEFAULT_VAULT, show_default=True, help="Path to vault file.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.argument("key")
@click.argument("value")
def set(vault: str, password: str, key: str, value: str) -> None:  # noqa: A001
    """Store a secret KEY=VALUE in the vault."""
    v = get_vault(vault, password)
    v.set(key, value)
    click.echo(f"Stored '{key}'.")


@cli.command("get")
@click.option("--vault", default=DEFAULT_VAULT, show_default=True, help="Path to vault file.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.argument("key")
def get(vault: str, password: str, key: str) -> None:  # noqa: A001
    """Retrieve a secret by KEY from the vault."""
    v = get_vault(vault, password)
    value = v.get(key)
    if value is None:
        click.echo(f"Key '{key}' not found.", err=True)
        sys.exit(1)
    click.echo(value)


@cli.command("list")
@click.option("--vault", default=DEFAULT_VAULT, show_default=True, help="Path to vault file.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def list_keys(vault: str, password: str) -> None:
    """List all keys stored in the vault."""
    v = get_vault(vault, password)
    keys = v.keys()
    if not keys:
        click.echo("No secrets stored.")
    else:
        for key in sorted(keys):
            click.echo(key)


@cli.command("export")
@click.option("--vault", default=DEFAULT_VAULT, show_default=True, help="Path to vault file.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option(
    "--format",
    "fmt",
    default="dotenv",
    show_default=True,
    type=click.Choice(["dotenv", "shell", "json"], case_sensitive=False),
    help="Output format.",
)
@click.option("--output", "-o", default=None, help="Write output to FILE instead of stdout.")
def export(vault: str, password: str, fmt: str, output: str | None) -> None:
    """Export all secrets from the vault in the chosen format."""
    v = get_vault(vault, password)
    secrets = {key: v.get(key) for key in v.keys()}  # type: ignore[misc]
    result = export_secrets(secrets, fmt=fmt)  # type: ignore[arg-type]
    if output:
        Path(output).write_text(result)
        click.echo(f"Exported {len(secrets)} secret(s) to '{output}'.")
    else:
        click.echo(result, nl=False)
