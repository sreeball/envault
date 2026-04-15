"""CLI commands for category management."""
import click

from envault.category import (
    CategoryError,
    assign_category,
    remove_from_category,
    list_categories,
    keys_in_category,
)
from envault.cli import get_vault


@click.group("category")
def category_group():
    """Organise secrets into named categories."""


@category_group.command("assign")
@click.argument("key")
@click.argument("category")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def assign_cmd(key: str, category: str, vault_path: str):
    """Assign KEY to CATEGORY."""
    try:
        result = assign_category(vault_path, key, category)
        click.echo(f"Assigned '{key}' to category '{category}'.")
        click.echo(f"Members: {', '.join(result['members'])}")
    except CategoryError as exc:
        raise click.ClickException(str(exc)) from exc


@category_group.command("remove")
@click.argument("key")
@click.argument("category")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def remove_cmd(key: str, category: str, vault_path: str):
    """Remove KEY from CATEGORY."""
    try:
        remaining = remove_from_category(vault_path, key, category)
        click.echo(f"Removed '{key}' from category '{category}'.")
        if remaining:
            click.echo(f"Remaining: {', '.join(remaining)}")
        else:
            click.echo("Category is now empty and has been deleted.")
    except CategoryError as exc:
        raise click.ClickException(str(exc)) from exc


@category_group.command("list")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def list_cmd(vault_path: str):
    """List all categories and their members."""
    cats = list_categories(vault_path)
    if not cats:
        click.echo("No categories defined.")
        return
    for cat, members in sorted(cats.items()):
        click.echo(f"{cat}: {', '.join(members)}")


@category_group.command("keys")
@click.argument("category")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def keys_cmd(category: str, vault_path: str):
    """List all keys in CATEGORY."""
    try:
        keys = keys_in_category(vault_path, category)
        if not keys:
            click.echo(f"No keys in category '{category}'.")
            return
        for k in keys:
            click.echo(k)
    except CategoryError as exc:
        raise click.ClickException(str(exc)) from exc
