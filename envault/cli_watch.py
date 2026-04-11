"""CLI commands for vault file watching."""

import click
from pathlib import Path

from envault.cli import get_vault
from envault.watch import WatchError, watch
from envault.hooks import _load_hooks, _hooks_path
import subprocess


@click.group("watch")
def watch_group():
    """Watch a vault for changes and react automatically."""


@watch_group.command("start")
@click.option("--vault", "vault_path", default="vault.db", show_default=True, help="Path to vault file.")
@click.option("--interval", default=1.0, show_default=True, help="Poll interval in seconds.")
@click.option("--timeout", default=None, type=float, help="Stop after N seconds (default: run forever).")
@click.option("--fire-hooks", is_flag=True, default=False, help="Fire registered hooks on each change.")
def start_cmd(vault_path, interval, timeout, fire_hooks):
    """Watch a vault file and print a message on every change."""
    path = Path(vault_path)
    click.echo(f"Watching {path} (interval={interval}s) ...")

    def _on_change(p: Path):
        click.echo(f"[envault] Change detected in {p}")
        if fire_hooks:
            hooks_file = _hooks_path(p)
            if hooks_file.exists():
                import json
                hooks = json.loads(hooks_file.read_text())
                for event, commands in hooks.items():
                    if event == "on_change":
                        for cmd in commands:
                            click.echo(f"  -> running hook: {cmd}")
                            subprocess.run(cmd, shell=True)

    try:
        total = watch(path, _on_change, interval=interval, timeout=timeout)
        click.echo(f"Watch ended. {total} change(s) detected.")
    except WatchError as exc:
        raise click.ClickException(str(exc))
    except KeyboardInterrupt:
        click.echo("\nWatch stopped.")
