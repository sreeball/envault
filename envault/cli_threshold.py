"""CLI commands for threshold management."""

from __future__ import annotations

import click

from envault.cli import get_vault
from envault.threshold import (
    ThresholdError,
    check_threshold,
    get_threshold,
    list_thresholds,
    remove_threshold,
    set_threshold,
)


@click.group("threshold")
def threshold_group() -> None:
    """Manage numeric thresholds on secrets."""


@threshold_group.command("set")
@click.argument("key")
@click.argument("operator", type=click.Choice(["lt", "lte", "gt", "gte", "eq", "ne"]))
@click.argument("value", type=float)
@click.option("--note", default="", help="Optional note about this threshold.")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True)
@click.option("--password", envvar="ENVAULT_PASSWORD", required=True, hide_input=True)
def set_cmd(key, operator, value, note, vault_path, password):
    """Set a threshold on KEY using OPERATOR and VALUE."""
    get_vault(vault_path, password)  # validate credentials
    try:
        entry = set_threshold(vault_path, key, operator, value, note)
        click.echo(f"Threshold set: {key} {operator} {entry['value']}")
    except ThresholdError as exc:
        raise click.ClickException(str(exc)) from exc


@threshold_group.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True)
@click.option("--password", envvar="ENVAULT_PASSWORD", required=True, hide_input=True)
def get_cmd(key, vault_path, password):
    """Show the threshold for KEY."""
    get_vault(vault_path, password)
    entry = get_threshold(vault_path, key)
    if entry is None:
        click.echo(f"No threshold set for '{key}'.")
    else:
        click.echo(f"{key}: {entry['operator']} {entry['value']}  # {entry['note']}")


@threshold_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True)
@click.option("--password", envvar="ENVAULT_PASSWORD", required=True, hide_input=True)
def remove_cmd(key, vault_path, password):
    """Remove the threshold for KEY."""
    get_vault(vault_path, password)
    removed = remove_threshold(vault_path, key)
    if removed:
        click.echo(f"Threshold for '{key}' removed.")
    else:
        click.echo(f"No threshold found for '{key}'.")


@threshold_group.command("list")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True)
@click.option("--password", envvar="ENVAULT_PASSWORD", required=True, hide_input=True)
def list_cmd(vault_path, password):
    """List all thresholds."""
    get_vault(vault_path, password)
    entries = list_thresholds(vault_path)
    if not entries:
        click.echo("No thresholds defined.")
    else:
        for e in entries:
            click.echo(f"{e['key']}: {e['operator']} {e['value']}  # {e['note']}")


@threshold_group.command("check")
@click.argument("key")
@click.argument("actual", type=float)
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True)
@click.option("--password", envvar="ENVAULT_PASSWORD", required=True, hide_input=True)
def check_cmd(key, actual, vault_path, password):
    """Check whether ACTUAL satisfies KEY's threshold."""
    get_vault(vault_path, password)
    try:
        ok = check_threshold(vault_path, key, actual)
        status = "PASS" if ok else "FAIL"
        click.echo(f"{status}: {key} threshold check for value {actual}")
        if not ok:
            raise SystemExit(1)
    except ThresholdError as exc:
        raise click.ClickException(str(exc)) from exc
