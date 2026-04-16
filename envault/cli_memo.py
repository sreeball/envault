"""CLI commands for key memos."""

import click
from .memo import add_memo, get_memos, clear_memos, list_all, MemoError


@click.group("memo")
def memo_group():
    """Attach short memos to vault keys."""


@memo_group.command("add")
@click.argument("vault_path")
@click.argument("key")
@click.argument("text")
def add_cmd(vault_path, key, text):
    """Add a memo to KEY."""
    try:
        entry = add_memo(vault_path, key, text)
        click.echo(f"Memo added at {entry['created_at']}.")
    except MemoError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@memo_group.command("get")
@click.argument("vault_path")
@click.argument("key")
def get_cmd(vault_path, key):
    """List memos for KEY."""
    memos = get_memos(vault_path, key)
    if not memos:
        click.echo(f"No memos for '{key}'.")
        return
    for i, m in enumerate(memos, 1):
        click.echo(f"{i}. [{m['created_at']}] {m['text']}")


@memo_group.command("clear")
@click.argument("vault_path")
@click.argument("key")
def clear_cmd(vault_path, key):
    """Remove all memos for KEY."""
    count = clear_memos(vault_path, key)
    click.echo(f"Cleared {count} memo(s) for '{key}'.")


@memo_group.command("list")
@click.argument("vault_path")
def list_cmd(vault_path):
    """List all memos across all keys."""
    data = list_all(vault_path)
    if not data:
        click.echo("No memos found.")
        return
    for key, memos in data.items():
        click.echo(f"{key}: {len(memos)} memo(s)")
        for m in memos:
            click.echo(f"  [{m['created_at']}] {m['text']}")
