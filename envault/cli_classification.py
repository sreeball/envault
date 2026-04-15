"""CLI commands for secret classification."""

import click
from envault.classification import (
    ClassificationError,
    classify,
    get_classification,
    remove_classification,
    list_by_level,
    all_classifications,
    CLASSIFICATION_LEVELS,
)
from envault.cli import get_vault


@click.group("classification")
def classification_group():
    """Manage secret classification levels."""


@classification_group.command("set")
@click.argument("key")
@click.argument("level", type=click.Choice(CLASSIFICATION_LEVELS))
@click.option("--reason", default="", help="Reason for this classification.")
@click.option("--vault", "vault_path", envvar="ENVAULT_PATH", required=True)
def set_cmd(key, level, reason, vault_path):
    """Classify a secret key at the given level."""
    try:
        entry = classify(vault_path, key, level, reason=reason)
        click.echo(f"Classified '{key}' as '{entry['level']}'.")
    except ClassificationError as exc:
        raise click.ClickException(str(exc))


@classification_group.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", envvar="ENVAULT_PATH", required=True)
def get_cmd(key, vault_path):
    """Show the classification for a key."""
    entry = get_classification(vault_path, key)
    if entry is None:
        click.echo(f"No classification set for '{key}'.")
    else:
        click.echo(f"Level : {entry['level']}")
        if entry.get("reason"):
            click.echo(f"Reason: {entry['reason']}")


@classification_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", envvar="ENVAULT_PATH", required=True)
def remove_cmd(key, vault_path):
    """Remove the classification for a key."""
    removed = remove_classification(vault_path, key)
    if removed:
        click.echo(f"Classification removed for '{key}'.")
    else:
        click.echo(f"No classification found for '{key}'.")


@classification_group.command("list")
@click.option("--level", type=click.Choice(CLASSIFICATION_LEVELS), default=None)
@click.option("--vault", "vault_path", envvar="ENVAULT_PATH", required=True)
def list_cmd(level, vault_path):
    """List classified keys, optionally filtered by level."""
    try:
        if level:
            keys = list_by_level(vault_path, level)
            if not keys:
                click.echo(f"No keys classified as '{level}'.")
            else:
                for k in keys:
                    click.echo(k)
        else:
            data = all_classifications(vault_path)
            if not data:
                click.echo("No classifications recorded.")
            else:
                for k, v in sorted(data.items()):
                    click.echo(f"{k}: {v['level']}")
    except ClassificationError as exc:
        raise click.ClickException(str(exc))
