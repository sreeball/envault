"""CLI commands for managing secret groups."""

import click
from envault.cli import get_vault
from envault.group import (
    GroupError,
    create_group,
    add_key_to_group,
    remove_key_from_group,
    delete_group,
    list_groups,
    get_group,
)


@click.group(name="group")
def group_cmd():
    """Manage secret groups."""


@group_cmd.command(name="create")
@click.argument("group")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def create_cmd(group: str, vault_path: str):
    """Create a new empty group."""
    try:
        create_group(vault_path, group)
        click.echo(f"Group '{group}' created.")
    except GroupError as exc:
        raise click.ClickException(str(exc))


@group_cmd.command(name="add")
@click.argument("group")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def add_cmd(group: str, key: str, vault_path: str):
    """Add a key to a group."""
    try:
        result = add_key_to_group(vault_path, group, key)
        click.echo(f"Added '{key}' to group '{group}'. Keys: {result[group]}")
    except GroupError as exc:
        raise click.ClickException(str(exc))


@group_cmd.command(name="remove")
@click.argument("group")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def remove_cmd(group: str, key: str, vault_path: str):
    """Remove a key from a group."""
    try:
        remove_key_from_group(vault_path, group, key)
        click.echo(f"Removed '{key}' from group '{group}'.")
    except GroupError as exc:
        raise click.ClickException(str(exc))


@group_cmd.command(name="delete")
@click.argument("group")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def delete_cmd(group: str, vault_path: str):
    """Delete an entire group."""
    try:
        delete_group(vault_path, group)
        click.echo(f"Group '{group}' deleted.")
    except GroupError as exc:
        raise click.ClickException(str(exc))


@group_cmd.command(name="list")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def list_cmd(vault_path: str):
    """List all groups and their keys."""
    groups = list_groups(vault_path)
    if not groups:
        click.echo("No groups defined.")
        return
    for name, keys in groups.items():
        click.echo(f"{name}: {', '.join(keys) if keys else '(empty)'}")


@group_cmd.command(name="keys")
@click.argument("group")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def keys_cmd(group: str, vault_path: str):
    """List keys in a specific group."""
    try:
        keys = get_group(vault_path, group)
        if not keys:
            click.echo(f"Group '{group}' is empty.")
        else:
            for k in keys:
                click.echo(k)
    except GroupError as exc:
        raise click.ClickException(str(exc))
