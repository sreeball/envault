"""CLI commands for the envault recycle bin."""
from __future__ import annotations

import click

from envault.cli import get_vault
from envault.recycle import (
    RecycleError,
    list_bin,
    purge,
    purge_all,
    restore,
    soft_delete,
)


@click.group("recycle")
def recycle_group() -> None:
    """Manage the vault recycle bin (soft-delete)."""


@recycle_group.command("delete")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.json", show_default=True)
@click.option("--password", prompt=True, hide_input=True)
def delete_cmd(key: str, vault_path: str, password: str) -> None:
    """Soft-delete KEY, moving it to the recycle bin."""
    vault = get_vault(vault_path, password)
    try:
        raw = vault._load_raw()
        if key not in raw:
            raise click.ClickException(f"Key '{key}' not found in vault.")
        payload = raw[key]
        soft_delete(vault_path, key, payload)
        del raw[key]
        vault._save_raw(raw)
        click.echo(f"Moved '{key}' to recycle bin.")
    except RecycleError as exc:
        raise click.ClickException(str(exc)) from exc


@recycle_group.command("restore")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.json", show_default=True)
def restore_cmd(key: str, vault_path: str) -> None:
    """Restore KEY from the recycle bin back into the vault."""
    try:
        entry = restore(vault_path, key)
        import json
        from pathlib import Path
        p = Path(vault_path)
        data = json.loads(p.read_text()) if p.exists() else {}
        data[key] = entry["payload"]
        p.write_text(json.dumps(data, indent=2))
        click.echo(f"Restored '{key}' to vault.")
    except RecycleError as exc:
        raise click.ClickException(str(exc)) from exc


@recycle_group.command("list")
@click.option("--vault", "vault_path", default="vault.json", show_default=True)
def list_cmd(vault_path: str) -> None:
    """List all keys currently in the recycle bin."""
    entries = list_bin(vault_path)
    if not entries:
        click.echo("Recycle bin is empty.")
        return
    for e in entries:
        click.echo(f"{e['key']}  (deleted {e['deleted_at']})")


@recycle_group.command("purge")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.json", show_default=True)
def purge_cmd(key: str, vault_path: str) -> None:
    """Permanently remove KEY from the recycle bin."""
    try:
        purge(vault_path, key)
        click.echo(f"Permanently deleted '{key}' from recycle bin.")
    except RecycleError as exc:
        raise click.ClickException(str(exc)) from exc


@recycle_group.command("purge-all")
@click.option("--vault", "vault_path", default="vault.json", show_default=True)
@click.confirmation_option(prompt="Permanently delete all items in the recycle bin?")
def purge_all_cmd(vault_path: str) -> None:
    """Permanently remove ALL entries from the recycle bin."""
    count = purge_all(vault_path)
    click.echo(f"Purged {count} item(s) from recycle bin.")
