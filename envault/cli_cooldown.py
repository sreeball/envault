"""CLI commands for managing key cooldown periods."""

from __future__ import annotations

import click

from envault.cli import get_vault
from envault.cooldown import (
    CooldownError,
    is_cooling_down,
    list_cooldowns,
    remove_cooldown,
    set_cooldown,
)


@click.group("cooldown")
def cooldown_group() -> None:
    """Manage cooldown periods for vault keys."""


@cooldown_group.command("set")
@click.argument("key")
@click.argument("seconds", type=int)
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
def set_cmd(key: str, seconds: int, vault_path: str) -> None:
    """Set a cooldown of SECONDS for KEY."""
    try:
        entry = set_cooldown(vault_path, key, seconds)
        click.echo(f"Cooldown set for '{key}': {seconds}s (expires {entry['expires_at']})")
    except CooldownError as exc:
        raise click.ClickException(str(exc)) from exc


@cooldown_group.command("check")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
def check_cmd(key: str, vault_path: str) -> None:
    """Check whether KEY is currently cooling down."""
    if is_cooling_down(vault_path, key):
        click.echo(f"'{key}' is cooling down.")
        raise SystemExit(1)
    click.echo(f"'{key}' is not cooling down.")


@cooldown_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
def remove_cmd(key: str, vault_path: str) -> None:
    """Remove the cooldown for KEY."""
    removed = remove_cooldown(vault_path, key)
    if removed:
        click.echo(f"Cooldown removed for '{key}'.")
    else:
        click.echo(f"No cooldown found for '{key}'.")


@cooldown_group.command("list")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
@click.option("--active-only", is_flag=True, default=False)
def list_cmd(vault_path: str, active_only: bool) -> None:
    """List all cooldown entries."""
    entries = list_cooldowns(vault_path)
    if active_only:
        entries = [e for e in entries if e["active"]]
    if not entries:
        click.echo("No cooldowns found.")
        return
    for e in entries:
        status = "ACTIVE" if e["active"] else "expired"
        click.echo(f"{e['key']:30s} {e['seconds']:>6}s  {status}  expires={e['expires_at']}")
