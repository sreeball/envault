"""CLI commands for managing key deprecations."""

import click

from .deprecation import (
    DeprecationError,
    deprecate_key,
    undeprecate_key,
    get_deprecation,
    list_deprecated,
)
from .cli import get_vault


@click.group("deprecation")
def deprecation_group():
    """Manage deprecated vault keys."""


@deprecation_group.command("mark")
@click.argument("key")
@click.argument("reason")
@click.option("--replacement", "-r", default=None, help="Suggested replacement key.")
@click.pass_context
def mark_cmd(ctx, key, reason, replacement):
    """Mark KEY as deprecated with REASON."""
    vault_path = get_vault(ctx)
    try:
        entry = deprecate_key(vault_path, key, reason, replacement=replacement)
        click.echo(f"Deprecated '{key}': {entry['reason']}")
        if entry["replacement"]:
            click.echo(f"  Use '{entry['replacement']}' instead.")
    except DeprecationError as exc:
        raise click.ClickException(str(exc))


@deprecation_group.command("unmark")
@click.argument("key")
@click.pass_context
def unmark_cmd(ctx, key):
    """Remove deprecation mark from KEY."""
    vault_path = get_vault(ctx)
    try:
        undeprecate_key(vault_path, key)
        click.echo(f"'{key}' is no longer deprecated.")
    except DeprecationError as exc:
        raise click.ClickException(str(exc))


@deprecation_group.command("get")
@click.argument("key")
@click.pass_context
def get_cmd(ctx, key):
    """Show deprecation info for KEY."""
    vault_path = get_vault(ctx)
    entry = get_deprecation(vault_path, key)
    if entry is None:
        click.echo(f"'{key}' is not deprecated.")
    else:
        click.echo(f"Reason: {entry['reason']}")
        if entry.get("replacement"):
            click.echo(f"Replacement: {entry['replacement']}")


@deprecation_group.command("list")
@click.pass_context
def list_cmd(ctx):
    """List all deprecated keys."""
    vault_path = get_vault(ctx)
    entries = list_deprecated(vault_path)
    if not entries:
        click.echo("No deprecated keys.")
        return
    for key, info in entries.items():
        replacement = f" -> {info['replacement']}" if info.get("replacement") else ""
        click.echo(f"{key}{replacement}: {info['reason']}")
