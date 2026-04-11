"""CLI commands for vault snapshots."""

import click

from envault.cli import get_vault
from envault.snapshot import (
    SnapshotError,
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
)


@click.group("snapshot")
def snapshot_group():
    """Create, list, restore, and delete vault snapshots."""


@snapshot_group.command("create")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True,
              help="Path to the vault file.")
@click.option("--password", envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
@click.option("--label", default="", help="Optional human-readable label.")
def create_cmd(vault_path, password, label):
    """Snapshot all secrets in the vault."""
    try:
        result = create_snapshot(vault_path, password, label=label)
        click.echo(f"Snapshot created: {result['snapshot']} ({result['count']} secrets)")
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc


@snapshot_group.command("list")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True,
              help="Path to the vault file.")
def list_cmd(vault_path):
    """List all snapshots for the vault."""
    snaps = list_snapshots(vault_path)
    if not snaps:
        click.echo("No snapshots found.")
        return
    for snap in snaps:
        label_part = f"  [{snap['label']}]" if snap["label"] else ""
        click.echo(f"{snap['timestamp']}{label_part}  {snap['count']} secrets  {snap['file']}")


@snapshot_group.command("restore")
@click.argument("snapshot_file")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True,
              help="Path to the vault file.")
@click.option("--password", envvar="ENVAULT_PASSWORD", prompt=True, hide_input=True)
def restore_cmd(snapshot_file, vault_path, password):
    """Restore vault secrets from SNAPSHOT_FILE."""
    try:
        result = restore_snapshot(vault_path, password, snapshot_file)
        click.echo(f"Restored {result['restored']} secrets from {result['from']}")
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc


@snapshot_group.command("delete")
@click.argument("snapshot_file")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True,
              help="Path to the vault file.")
@click.confirmation_option(prompt="Delete this snapshot?")
def delete_cmd(snapshot_file, vault_path):
    """Delete SNAPSHOT_FILE."""
    try:
        delete_snapshot(vault_path, snapshot_file)
        click.echo(f"Deleted snapshot: {snapshot_file}")
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc
