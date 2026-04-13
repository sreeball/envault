"""CLI commands for secret sharing."""
from __future__ import annotations

import click

from envault.cli import get_vault
from envault.sharing import SharingError, share_key, redeem_share, revoke_share, list_shares


@click.group("share")
def sharing_group() -> None:
    """Share individual secrets securely with other users."""


@sharing_group.command("create")
@click.argument("vault_path")
@click.argument("key")
@click.argument("recipient")
@click.password_option("--vault-password", prompt="Vault password", help="Password for the vault.")
@click.password_option("--share-password", prompt="Share password", help="Password for the share.")
@click.option("--ttl", default=86400, show_default=True, help="Share lifetime in seconds.")
def create_cmd(vault_path, key, recipient, vault_password, share_password, ttl):
    """Create a share for KEY and send it to RECIPIENT."""
    vault = get_vault(vault_path, vault_password)
    try:
        plaintext = vault.get(key)
    except KeyError:
        raise click.ClickException(f"key '{key}' not found in vault")
    try:
        entry = share_key(vault_path, key, plaintext, recipient, share_password, ttl_seconds=ttl)
    except SharingError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Share created for '{key}' → '{recipient}' (expires in {ttl}s).")
    click.echo(f"expires_at: {entry['expires_at']:.0f}")


@sharing_group.command("redeem")
@click.argument("vault_path")
@click.argument("key")
@click.argument("recipient")
@click.password_option("--share-password", prompt="Share password", help="Password for the share.")
def redeem_cmd(vault_path, key, recipient, share_password):
    """Redeem a share for KEY as RECIPIENT."""
    try:
        value = redeem_share(vault_path, key, recipient, share_password)
    except SharingError as exc:
        raise click.ClickException(str(exc))
    click.echo(value)


@sharing_group.command("revoke")
@click.argument("vault_path")
@click.argument("key")
@click.argument("recipient")
def revoke_cmd(vault_path, key, recipient):
    """Revoke all shares for KEY granted to RECIPIENT."""
    try:
        removed = revoke_share(vault_path, key, recipient)
    except SharingError as exc:
        raise click.ClickException(str(exc))
    if removed:
        click.echo(f"Revoked {removed} share(s) for '{key}' from '{recipient}'.")
    else:
        click.echo(f"No shares found for '{key}' / '{recipient}'.")


@sharing_group.command("list")
@click.argument("vault_path")
def list_cmd(vault_path):
    """List all active shares in the vault."""
    shares = list_shares(vault_path)
    if not shares:
        click.echo("No shares found.")
        return
    for key, entries in shares.items():
        for entry in entries:
            click.echo(f"{key}  →  {entry['recipient']}  expires={entry['expires_at']:.0f}")
