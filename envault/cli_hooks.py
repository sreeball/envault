"""CLI commands for managing vault operation hooks."""

from pathlib import Path

import click

from envault.hooks import HookError, fire, list_hooks, register_hook, unregister_hook


@click.group("hooks")
def hooks_group() -> None:
    """Manage pre/post hooks for vault operations."""


@hooks_group.command("add")
@click.option("--vault", "vault_path", required=True, type=click.Path(), help="Path to vault file.")
@click.argument("event")
@click.argument("command")
def add_cmd(vault_path: str, event: str, command: str) -> None:
    """Register COMMAND to run on EVENT (e.g. post_set)."""
    try:
        register_hook(Path(vault_path), event, command)
        click.echo(f"Hook registered: [{event}] -> {command}")
    except HookError as exc:
        raise click.ClickException(str(exc)) from exc


@hooks_group.command("remove")
@click.option("--vault", "vault_path", required=True, type=click.Path(), help="Path to vault file.")
@click.argument("event")
@click.argument("command")
def remove_cmd(vault_path: str, event: str, command: str) -> None:
    """Unregister COMMAND from EVENT."""
    try:
        unregister_hook(Path(vault_path), event, command)
        click.echo(f"Hook removed: [{event}] -> {command}")
    except HookError as exc:
        raise click.ClickException(str(exc)) from exc


@hooks_group.command("list")
@click.option("--vault", "vault_path", required=True, type=click.Path(), help="Path to vault file.")
def list_cmd(vault_path: str) -> None:
    """List all registered hooks."""
    hooks = list_hooks(Path(vault_path))
    if not hooks:
        click.echo("No hooks registered.")
        return
    for event, commands in sorted(hooks.items()):
        for cmd in commands:
            click.echo(f"  {event}: {cmd}")


@hooks_group.command("fire")
@click.option("--vault", "vault_path", required=True, type=click.Path(), help="Path to vault file.")
@click.argument("event")
def fire_cmd(vault_path: str, event: str) -> None:
    """Manually fire all hooks for EVENT."""
    try:
        executed = fire(Path(vault_path), event)
        if executed:
            click.echo(f"Fired {len(executed)} hook(s) for '{event}'.")
        else:
            click.echo(f"No hooks registered for '{event}'.")
    except HookError as exc:
        raise click.ClickException(str(exc)) from exc
