"""CLI commands for managing vault event notifications."""

from __future__ import annotations

import click

from envault.cli import get_vault
from envault.notify import NotifyError, fire, list_subscriptions, subscribe, unsubscribe


@click.group("notify", help="Manage event notification hooks.")
def notify_group() -> None:
    pass


@notify_group.command("subscribe")
@click.argument("vault_path")
@click.argument("event")
@click.argument("command")
def subscribe_cmd(vault_path: str, event: str, command: str) -> None:
    """Subscribe COMMAND to EVENT on VAULT_PATH."""
    try:
        result = subscribe(vault_path, event, command)
        click.echo(f"Subscribed to '{event}': {command}")
        click.echo(f"Total handlers: {len(result['all'])}")
    except NotifyError as exc:
        raise click.ClickException(str(exc)) from exc


@notify_group.command("unsubscribe")
@click.argument("vault_path")
@click.argument("event")
@click.argument("command")
def unsubscribe_cmd(vault_path: str, event: str, command: str) -> None:
    """Remove COMMAND from EVENT handlers."""
    try:
        remaining = unsubscribe(vault_path, event, command)
        click.echo(f"Removed handler. Remaining for '{event}': {len(remaining)}")
    except NotifyError as exc:
        raise click.ClickException(str(exc)) from exc


@notify_group.command("fire")
@click.argument("vault_path")
@click.argument("event")
@click.option("--context", "-c", multiple=True, metavar="KEY=VALUE",
              help="Context variables passed as ENVAULT_<KEY> env vars.")
def fire_cmd(vault_path: str, event: str, context: tuple[str, ...]) -> None:
    """Manually fire EVENT and run all registered handlers."""
    ctx: dict = {}
    for item in context:
        if "=" not in item:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {item}")
        k, v = item.split("=", 1)
        ctx[k] = v
    try:
        results = fire(vault_path, event, ctx or None)
        if not results:
            click.echo("No handlers registered for this event.")
            return
        for r in results:
            status = "OK" if r["returncode"] == 0 else f"EXIT {r['returncode']}"
            click.echo(f"[{status}] {r['command']}")
            if r["stdout"]:
                click.echo(f"  {r['stdout']}")
    except NotifyError as exc:
        raise click.ClickException(str(exc)) from exc


@notify_group.command("list")
@click.argument("vault_path")
def list_cmd(vault_path: str) -> None:
    """List all event subscriptions for VAULT_PATH."""
    subs = list_subscriptions(vault_path)
    if not subs:
        click.echo("No subscriptions found.")
        return
    for event, handlers in subs.items():
        click.echo(f"{event}:")
        for h in handlers:
            click.echo(f"  - {h}")
