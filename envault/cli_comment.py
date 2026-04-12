"""CLI commands for managing per-key comments."""

import click
from envault.cli import get_vault
from envault.comment import (
    CommentError,
    add_comment,
    get_comments,
    remove_comments,
    list_commented_keys,
)


@click.group("comment")
def comment_group():
    """Manage comments/annotations on vault keys."""


@comment_group.command("add")
@click.argument("key")
@click.argument("comment")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
def add_cmd(key: str, comment: str, vault_path: str):
    """Add a comment to KEY."""
    try:
        comments = add_comment(vault_path, key, comment)
        click.echo(f"Comment added to '{key}'. Total comments: {len(comments)}")
    except CommentError as exc:
        raise click.ClickException(str(exc))


@comment_group.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
def get_cmd(key: str, vault_path: str):
    """Show all comments for KEY."""
    comments = get_comments(vault_path, key)
    if not comments:
        click.echo(f"No comments for '{key}'.")
        return
    for i, c in enumerate(comments, 1):
        click.echo(f"  {i}. {c}")


@comment_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
def remove_cmd(key: str, vault_path: str):
    """Remove all comments for KEY."""
    try:
        remove_comments(vault_path, key)
        click.echo(f"All comments removed from '{key}'.")
    except CommentError as exc:
        raise click.ClickException(str(exc))


@comment_group.command("list")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
def list_cmd(vault_path: str):
    """List all keys that have comments."""
    annotated = list_commented_keys(vault_path)
    if not annotated:
        click.echo("No comments found.")
        return
    for key, comments in annotated.items():
        click.echo(f"{key} ({len(comments)} comment{'s' if len(comments) != 1 else ''}):")
        for c in comments:
            click.echo(f"    - {c}")
