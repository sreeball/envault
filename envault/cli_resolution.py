"""CLI commands for managing key resolution order."""

import click

from envault.cli import get_vault
from envault.resolution import (
    ResolutionError,
    get_resolution_order,
    list_resolution,
    remove_resolution,
    resolve_value,
    set_resolution_order,
)


@click.group("resolution")
def resolution_group():
    """Manage key resolution order across vault sources."""


@resolution_group.command("set")
@click.argument("key")
@click.argument("sources", nargs=-1, required=True)
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_PATH")
def set_cmd(key, sources, vault_path):
    """Set the resolution order for KEY using the given SOURCES (vault paths)."""
    try:
        result = set_resolution_order(vault_path, key, list(sources))
        click.echo(f"Resolution order set for '{result['key']}': {result['sources']}")
    except ResolutionError as exc:
        raise click.ClickException(str(exc))


@resolution_group.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_PATH")
def get_cmd(key, vault_path):
    """Show the resolution source order for KEY."""
    sources = get_resolution_order(vault_path, key)
    if not sources:
        click.echo(f"No resolution order configured for '{key}'.")
    else:
        for i, src in enumerate(sources, 1):
            click.echo(f"{i}. {src}")


@resolution_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_PATH")
def remove_cmd(key, vault_path):
    """Remove the resolution order entry for KEY."""
    removed = remove_resolution(vault_path, key)
    if removed:
        click.echo(f"Resolution order removed for '{key}'.")
    else:
        click.echo(f"No resolution order found for '{key}'.")


@resolution_group.command("resolve")
@click.argument("key")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_PATH")
@click.option("--password", required=True, envvar="ENVAULT_PASSWORD", hide_input=True)
def resolve_cmd(key, vault_path, password):
    """Resolve and print the value for KEY using the configured source order."""
    try:
        value = resolve_value(vault_path, key, password)
        click.echo(value)
    except ResolutionError as exc:
        raise click.ClickException(str(exc))


@resolution_group.command("list")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_PATH")
def list_cmd(vault_path):
    """List all configured resolution orders."""
    data = list_resolution(vault_path)
    if not data:
        click.echo("No resolution orders configured.")
        return
    for key, entry in data.items():
        sources_str = " -> ".join(entry.get("sources", []))
        click.echo(f"{key}: {sources_str}")
