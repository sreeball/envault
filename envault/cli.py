import sys
import click
from pathlib import Path
from envault.vault import Vault

DEFAULT_VAULT_PATH = ".envault"


def get_vault(vault_path: str, password: str) -> Vault:
    return Vault(path=vault_path, password=password)


@click.group()
def cli():
    """envault — Securely manage and sync environment variables."""
    pass


@cli.command()
@click.argument("key")
@click.argument("value")
@click.option("--vault", default=DEFAULT_VAULT_PATH, help="Path to vault file.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def set(key, value, vault, password):
    """Set an environment variable in the vault."""
    v = get_vault(vault, password)
    v.set(key, value)
    click.echo(f"✔ Set '{key}' in vault.")


@cli.command()
@click.argument("key")
@click.option("--vault", default=DEFAULT_VAULT_PATH, help="Path to vault file.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def get(key, vault, password):
    """Get an environment variable from the vault."""
    v = get_vault(vault, password)
    value = v.get(key)
    if value is None:
        click.echo(f"Key '{key}' not found.", err=True)
        sys.exit(1)
    click.echo(value)


@cli.command(name="list")
@click.option("--vault", default=DEFAULT_VAULT_PATH, help="Path to vault file.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def list_keys(vault, password):
    """List all keys stored in the vault."""
    v = get_vault(vault, password)
    keys = v.keys()
    if not keys:
        click.echo("No variables stored in vault.")
    else:
        for key in sorted(keys):
            click.echo(key)


@cli.command()
@click.argument("key")
@click.option("--vault", default=DEFAULT_VAULT_PATH, help="Path to vault file.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def delete(key, vault, password):
    """Delete an environment variable from the vault."""
    v = get_vault(vault, password)
    removed = v.delete(key)
    if not removed:
        click.echo(f"Key '{key}' not found.", err=True)
        sys.exit(1)
    click.echo(f"✔ Deleted '{key}' from vault.")


if __name__ == "__main__":
    cli()
