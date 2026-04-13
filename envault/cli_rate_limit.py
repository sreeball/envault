"""CLI commands for managing vault rate limits."""

import click
from pathlib import Path

from .rate_limit import (
    RateLimitError,
    set_limit,
    remove_limit,
    list_limits,
    check_and_record,
)


@click.group("rate-limit", help="Manage operation rate limits for a vault.")
def rate_limit_group():
    pass


@rate_limit_group.command("set")
@click.argument("vault_path", type=click.Path())
@click.argument("operation")
@click.argument("max_calls", type=int)
@click.argument("window_seconds", type=int)
def set_cmd(vault_path, operation, max_calls, window_seconds):
    """Set a rate limit for OPERATION (e.g. get, set, delete)."""
    try:
        entry = set_limit(Path(vault_path), operation, max_calls, window_seconds)
        click.echo(
            f"Rate limit set: '{operation}' — {entry['max_calls']} calls "
            f"per {entry['window_seconds']}s"
        )
    except RateLimitError as exc:
        raise click.ClickException(str(exc))


@rate_limit_group.command("remove")
@click.argument("vault_path", type=click.Path())
@click.argument("operation")
def remove_cmd(vault_path, operation):
    """Remove the rate limit for OPERATION."""
    try:
        remove_limit(Path(vault_path), operation)
        click.echo(f"Rate limit for '{operation}' removed.")
    except RateLimitError as exc:
        raise click.ClickException(str(exc))


@rate_limit_group.command("list")
@click.argument("vault_path", type=click.Path())
def list_cmd(vault_path):
    """List all configured rate limits."""
    limits = list_limits(Path(vault_path))
    if not limits:
        click.echo("No rate limits configured.")
        return
    for op, cfg in limits.items():
        click.echo(f"  {op}: {cfg['max_calls']} calls / {cfg['window_seconds']}s")


@rate_limit_group.command("check")
@click.argument("vault_path", type=click.Path())
@click.argument("operation")
def check_cmd(vault_path, operation):
    """Check and record a call for OPERATION (for testing limits)."""
    try:
        result = check_and_record(Path(vault_path), operation)
        if result["remaining"] is None:
            click.echo(f"'{operation}' has no rate limit configured.")
        else:
            click.echo(
                f"Allowed. {result['remaining']} of {result['limit']} calls remaining."
            )
    except RateLimitError as exc:
        raise click.ClickException(str(exc))
