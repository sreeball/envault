"""CLI commands for vault locking."""

import click

from .cli import get_vault
from .lock import LockError, assert_unlocked, is_locked, lock_info, lock_vault, unlock_vault


@click.group("lock", help="Lock and unlock a vault to prevent modifications.")
def lock_group() -> None:
    pass


@lock_group.command("acquire")
@click.option("--vault", "vault_path", required=True, help="Path to vault file.")
@click.option("--reason", default="", help="Reason for locking.")
@click.option("--actor", default="user", help="Who is locking the vault.")
def acquire_cmd(vault_path: str, reason: str, actor: str) -> None:
    """Lock the vault."""
    try:
        entry = lock_vault(vault_path, reason=reason, actor=actor)
        click.echo(f"Vault locked at {entry['locked_at']} by {entry['actor']}.")
        if reason:
            click.echo(f"Reason: {reason}")
    except LockError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@lock_group.command("release")
@click.option("--vault", "vault_path", required=True, help="Path to vault file.")
def release_cmd(vault_path: str) -> None:
    """Unlock the vault."""
    try:
        entry = unlock_vault(vault_path)
        click.echo(f"Vault unlocked at {entry['unlocked_at']}.")
    except LockError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@lock_group.command("status")
@click.option("--vault", "vault_path", required=True, help="Path to vault file.")
def status_cmd(vault_path: str) -> None:
    """Show lock status of the vault."""
    info = lock_info(vault_path)
    if info is None:
        click.echo("Vault is unlocked.")
    else:
        click.echo(f"Vault is LOCKED.")
        click.echo(f"  Locked at : {info['locked_at']}")
        click.echo(f"  Actor     : {info['actor']}")
        click.echo(f"  Reason    : {info.get('reason') or '(none)'}")
