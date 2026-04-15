"""CLI commands for the forecast feature."""
import click
from envault.cli import get_vault
from envault.forecast import build_forecast, summary


@click.group("forecast")
def forecast_group():
    """Preview upcoming secret expirations and reminders."""


@forecast_group.command("show")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True,
              help="Path to vault file.")
@click.option("--horizon", default=30, show_default=True,
              help="Look-ahead window in days.")
@click.option("--event", default=None,
              type=click.Choice(["expiry", "rotation", "reminder"]),
              help="Filter by event type.")
def show_cmd(vault_path: str, horizon: int, event):
    """Show secrets with upcoming events within HORIZON days."""
    entries = build_forecast(vault_path, horizon_days=horizon)
    if event:
        entries = [e for e in entries if e.event == event]
    if not entries:
        click.echo(f"No upcoming events within {horizon} days.")
        return
    for e in entries:
        note_str = f"  # {e.note}" if e.note else ""
        click.echo(
            f"[{e.event.upper():8s}] {e.key:30s}  due {e.due_at}  "
            f"({e.days_remaining}d)  [{e.source}]{note_str}"
        )


@forecast_group.command("summary")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True,
              help="Path to vault file.")
@click.option("--horizon", default=30, show_default=True,
              help="Look-ahead window in days.")
def summary_cmd(vault_path: str, horizon: int):
    """Print a count breakdown of upcoming events."""
    entries = build_forecast(vault_path, horizon_days=horizon)
    s = summary(entries)
    click.echo(f"Total upcoming events: {s['total']}")
    for event_type, count in s["by_event"].items():
        click.echo(f"  {event_type}: {count}")
