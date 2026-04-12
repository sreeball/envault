"""CLI commands for managing secret reminders."""

import click

from .reminder import (
    ReminderError,
    add_reminder,
    due_reminders,
    list_reminders,
    mark_fired,
    remove_reminder,
)


@click.group("reminder", help="Manage reminders to rotate or review secrets.")
def reminder_group() -> None:
    pass


@reminder_group.command("add")
@click.argument("key")
@click.argument("days", type=int)
@click.option("--message", "-m", default="", help="Reminder message.")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
def add_cmd(key: str, days: int, message: str, vault_path: str) -> None:
    """Add a reminder for KEY due in DAYS days."""
    try:
        entry = add_reminder(vault_path, key, message, days=days)
        click.echo(f"Reminder set for '{key}' due at {entry['due_at']}.")
    except ReminderError as exc:
        raise click.ClickException(str(exc))


@reminder_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
def remove_cmd(key: str, vault_path: str) -> None:
    """Remove the reminder for KEY."""
    try:
        remove_reminder(vault_path, key)
        click.echo(f"Reminder for '{key}' removed.")
    except ReminderError as exc:
        raise click.ClickException(str(exc))


@reminder_group.command("list")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
def list_cmd(vault_path: str) -> None:
    """List all reminders."""
    reminders = list_reminders(vault_path)
    if not reminders:
        click.echo("No reminders configured.")
        return
    for r in reminders:
        status = "[fired]" if r["fired"] else "[pending]"
        click.echo(f"{status} {r['key']:30s} due={r['due_at']}  {r['message']}")


@reminder_group.command("due")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
def due_cmd(vault_path: str) -> None:
    """Show reminders that are currently due."""
    due = due_reminders(vault_path)
    if not due:
        click.echo("No reminders due.")
        return
    for r in due:
        click.echo(f"DUE  {r['key']:30s} {r['message']}  (was due {r['due_at']})")


@reminder_group.command("fire")
@click.argument("key")
@click.option("--vault", "vault_path", required=True, envvar="ENVAULT_VAULT", help="Path to vault file.")
def fire_cmd(key: str, vault_path: str) -> None:
    """Mark the reminder for KEY as fired."""
    try:
        mark_fired(vault_path, key)
        click.echo(f"Reminder for '{key}' marked as fired.")
    except ReminderError as exc:
        raise click.ClickException(str(exc))
