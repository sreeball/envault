"""CLI commands for the evidence module."""

import click
from envault.evidence import attach, detach, list_evidence, clear_evidence, EvidenceError
from envault.cli import get_vault


@click.group("evidence")
def evidence_group():
    """Manage evidence attached to vault keys."""


@evidence_group.command("attach")
@click.argument("key")
@click.argument("description")
@click.option("--source", default="", help="Origin or URL of the evidence.")
@click.option(
    "--type",
    "evidence_type",
    default="note",
    help="Type of evidence (note, link, file, etc.).",
)
@click.pass_context
def attach_cmd(ctx, key, description, source, evidence_type):
    """Attach evidence to KEY."""
    vault = get_vault(ctx)
    try:
        entry = attach(vault.path, key, description, source=source, evidence_type=evidence_type)
        click.echo(f"Attached evidence {entry['id']} to '{key}'.")
    except EvidenceError as exc:
        raise click.ClickException(str(exc))


@evidence_group.command("detach")
@click.argument("key")
@click.argument("evidence_id")
@click.pass_context
def detach_cmd(ctx, key, evidence_id):
    """Remove evidence EVIDENCE_ID from KEY."""
    vault = get_vault(ctx)
    removed = detach(vault.path, key, evidence_id)
    if removed:
        click.echo(f"Removed evidence {evidence_id} from '{key}'.")
    else:
        click.echo(f"No evidence with id {evidence_id} found for '{key}'.")


@evidence_group.command("list")
@click.argument("key")
@click.pass_context
def list_cmd(ctx, key):
    """List all evidence attached to KEY."""
    vault = get_vault(ctx)
    entries = list_evidence(vault.path, key)
    if not entries:
        click.echo(f"No evidence found for '{key}'.")
        return
    for e in entries:
        click.echo(f"[{e['id']}] ({e['type']}) {e['description']}")
        if e.get("source"):
            click.echo(f"  source: {e['source']}")
        click.echo(f"  attached_at: {e['attached_at']}")


@evidence_group.command("clear")
@click.argument("key")
@click.pass_context
def clear_cmd(ctx, key):
    """Remove all evidence from KEY."""
    vault = get_vault(ctx)
    count = clear_evidence(vault.path, key)
    click.echo(f"Cleared {count} evidence entry/entries from '{key}'.")
