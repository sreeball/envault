"""CLI commands for trigger management."""

import click
from envault.cli import get_vault
from envault.trigger import add_trigger, remove_trigger, fire_triggers, list_triggers, TriggerError, VALID_EVENTS


@click.group("trigger")
def trigger_group():
    """Manage event-based triggers on vault keys."""


@trigger_group.command("add")
@click.argument("key")
@click.argument("event")
@click.argument("command")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def add_cmd(key, event, command, vault_path):
    """Register COMMAND to run when EVENT occurs on KEY."""
    try:
        entry = add_trigger(vault_path, key, event, command)
        click.echo(f"Trigger added: [{entry['event']}] on '{entry['key']}' -> {entry['command']}")
    except TriggerError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@trigger_group.command("remove")
@click.argument("key")
@click.argument("event")
@click.argument("command")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def remove_cmd(key, event, command, vault_path):
    """Remove a registered trigger command."""
    removed = remove_trigger(vault_path, key, event, command)
    if removed:
        click.echo(f"Trigger removed: [{event}] on '{key}'")
    else:
        click.echo("Trigger not found.", err=True)
        raise SystemExit(1)


@trigger_group.command("list")
@click.argument("key", required=False)
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def list_cmd(key, vault_path):
    """List triggers, optionally filtered by KEY."""
    data = list_triggers(vault_path, key)
    if not data or all(not v for v in data.values()):
        click.echo("No triggers registered.")
        return
    for k, events in data.items():
        for event, commands in events.items():
            for cmd in commands:
                click.echo(f"{k}  [{event}]  {cmd}")


@trigger_group.command("fire")
@click.argument("key")
@click.argument("event")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def fire_cmd(key, event, vault_path):
    """Manually fire all triggers for KEY and EVENT."""
    results = fire_triggers(vault_path, key, event)
    if not results:
        click.echo("No triggers found.")
        return
    for r in results:
        status = "OK" if r["returncode"] == 0 else f"FAIL({r['returncode']})"
        click.echo(f"[{status}] {r['command']}")
        if r["stdout"]:
            click.echo(f"  stdout: {r['stdout']}")
        if r["stderr"]:
            click.echo(f"  stderr: {r['stderr']}")
