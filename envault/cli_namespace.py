"""CLI commands for namespace management."""

import click

from envault.cli import get_vault
from envault.namespace import (
    NamespaceError,
    add_to_namespace,
    delete_namespace,
    keys_in_namespace,
    list_namespaces,
    remove_from_namespace,
)


@click.group("namespace", help="Group secrets under logical namespaces.")
def namespace_group() -> None:
    pass


@namespace_group.command("add")
@click.argument("namespace")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def add_cmd(namespace: str, key: str, vault_path: str) -> None:
    """Add KEY to NAMESPACE."""
    try:
        result = add_to_namespace(vault_path, namespace, key)
        click.echo(f"Added '{key}' to namespace '{namespace}'.")
        click.echo(f"Keys: {', '.join(result['keys'])}")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@namespace_group.command("remove")
@click.argument("namespace")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def remove_cmd(namespace: str, key: str, vault_path: str) -> None:
    """Remove KEY from NAMESPACE."""
    try:
        remove_from_namespace(vault_path, namespace, key)
        click.echo(f"Removed '{key}' from namespace '{namespace}'.")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@namespace_group.command("list")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def list_cmd(vault_path: str) -> None:
    """List all namespaces and their keys."""
    data = list_namespaces(vault_path)
    if not data:
        click.echo("No namespaces defined.")
        return
    for ns, keys in data.items():
        click.echo(f"{ns}: {', '.join(keys) if keys else '(empty)'}")


@namespace_group.command("keys")
@click.argument("namespace")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def keys_cmd(namespace: str, vault_path: str) -> None:
    """List keys belonging to NAMESPACE."""
    try:
        keys = keys_in_namespace(vault_path, namespace)
        if keys:
            click.echo("\n".join(keys))
        else:
            click.echo(f"Namespace '{namespace}' is empty.")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@namespace_group.command("delete")
@click.argument("namespace")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def delete_cmd(namespace: str, vault_path: str) -> None:
    """Delete NAMESPACE (secrets are preserved)."""
    try:
        delete_namespace(vault_path, namespace)
        click.echo(f"Namespace '{namespace}' deleted.")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
