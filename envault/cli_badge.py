"""CLI commands for badge management."""

from __future__ import annotations

import click

from envault.badge import BadgeError, create_badge, get_badge, list_badges, remove_badge
from envault.cli import get_vault


@click.group("badge")
def badge_group() -> None:
    """Manage status badges for secret keys."""


@badge_group.command("create")
@click.argument("key")
@click.argument("label")
@click.option("--color", default="blue", show_default=True, help="Badge color.")
@click.option("--style", default="flat", show_default=True, help="Badge style.")
@click.pass_context
def create_cmd(ctx: click.Context, key: str, label: str, color: str, style: str) -> None:
    """Create or update a badge for KEY with LABEL."""
    vault = get_vault(ctx)
    try:
        entry = create_badge(vault.path, key, label, color=color, style=style)
        click.echo(f"Badge created: [{entry['style']}] {entry['label']} ({entry['color']})")
    except BadgeError as exc:
        raise click.ClickException(str(exc)) from exc


@badge_group.command("get")
@click.argument("key")
@click.pass_context
def get_cmd(ctx: click.Context, key: str) -> None:
    """Show badge definition for KEY."""
    vault = get_vault(ctx)
    try:
        entry = get_badge(vault.path, key)
        click.echo(f"key={entry['key']}  label={entry['label']}  color={entry['color']}  style={entry['style']}")
    except BadgeError as exc:
        raise click.ClickException(str(exc)) from exc


@badge_group.command("remove")
@click.argument("key")
@click.pass_context
def remove_cmd(ctx: click.Context, key: str) -> None:
    """Remove the badge definition for KEY."""
    vault = get_vault(ctx)
    try:
        remove_badge(vault.path, key)
        click.echo(f"Badge removed for '{key}'.")
    except BadgeError as exc:
        raise click.ClickException(str(exc)) from exc


@badge_group.command("list")
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    """List all badge definitions."""
    vault = get_vault(ctx)
    badges = list_badges(vault.path)
    if not badges:
        click.echo("No badges defined.")
        return
    for b in badges:
        click.echo(f"{b['key']:30s}  {b['label']:20s}  {b['color']:10s}  {b['style']}")
