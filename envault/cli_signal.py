"""CLI commands for managing key signals."""
import click
from envault.signal import emit_signal, get_signals, clear_signals, list_all, SignalError


@click.group("signal", help="Attach and manage signals on vault keys.")
def signal_group():
    pass


@signal_group.command("emit")
@click.argument("vault_path")
@click.argument("key")
@click.argument("signal_name")
@click.option("--payload", default="", help="Optional payload string.")
def emit_cmd(vault_path, key, signal_name, payload):
    """Emit a named signal for a key."""
    try:
        entry = emit_signal(vault_path, key, signal_name, payload)
        click.echo(f"Signal '{entry['signal']}' emitted for '{key}'.")
    except SignalError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@signal_group.command("get")
@click.argument("vault_path")
@click.argument("key")
def get_cmd(vault_path, key):
    """List signals recorded for a key."""
    signals = get_signals(vault_path, key)
    if not signals:
        click.echo(f"No signals for '{key}'.")
        return
    for s in signals:
        payload_part = f" [{s['payload']}]" if s['payload'] else ""
        click.echo(f"{s['signal']}{payload_part}")


@signal_group.command("clear")
@click.argument("vault_path")
@click.argument("key")
def clear_cmd(vault_path, key):
    """Clear all signals for a key."""
    count = clear_signals(vault_path, key)
    click.echo(f"Cleared {count} signal(s) for '{key}'.")


@signal_group.command("list")
@click.argument("vault_path")
def list_cmd(vault_path):
    """List all keys with signals."""
    data = list_all(vault_path)
    if not data:
        click.echo("No signals recorded.")
        return
    for key, signals in data.items():
        click.echo(f"{key}: {len(signals)} signal(s)")
