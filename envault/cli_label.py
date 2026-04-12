"""CLI commands for label management."""

import click
from envault.cli import get_vault
from envault.label import (
    LabelError,
    add_label,
    remove_label,
    get_labels,
    keys_with_label,
    all_labels,
)


@click.group("label")
def label_group():
    """Manage labels on vault secrets."""


@label_group.command("add")
@click.argument("key")
@click.argument("label")
@click.option("--vault", "vault_path", default="vault.json", show_default=True)
def add_cmd(key, label, vault_path):
    """Add a label to a secret key."""
    try:
        labels = add_label(vault_path, key, label)
        click.echo(f"Labels for '{key}': {', '.join(labels)}")
    except LabelError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@label_group.command("remove")
@click.argument("key")
@click.argument("label")
@click.option("--vault", "vault_path", default="vault.json", show_default=True)
def remove_cmd(key, label, vault_path):
    """Remove a label from a secret key."""
    try:
        labels = remove_label(vault_path, key, label)
        remaining = ", ".join(labels) if labels else "(none)"
        click.echo(f"Labels for '{key}': {remaining}")
    except LabelError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@label_group.command("list")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.json", show_default=True)
def list_cmd(key, vault_path):
    """List all labels for a secret key."""
    labels = get_labels(vault_path, key)
    if not labels:
        click.echo(f"No labels for '{key}'.")
    else:
        for lbl in labels:
            click.echo(lbl)


@label_group.command("find")
@click.argument("label")
@click.option("--vault", "vault_path", default="vault.json", show_default=True)
def find_cmd(label, vault_path):
    """Find all keys with a given label."""
    keys = keys_with_label(vault_path, label)
    if not keys:
        click.echo(f"No keys found with label '{label}'.")
    else:
        for k in keys:
            click.echo(k)


@label_group.command("all")
@click.option("--vault", "vault_path", default="vault.json", show_default=True)
def all_cmd(vault_path):
    """Show all labels across all keys."""
    data = all_labels(vault_path)
    if not data:
        click.echo("No labels defined.")
    else:
        for key, labels in sorted(data.items()):
            click.echo(f"{key}: {', '.join(labels)}")
