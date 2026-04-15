"""CLI commands for compliance tagging."""
import click

from .compliance import (
    ComplianceError,
    tag_compliant,
    remove_compliance,
    get_compliance,
    list_compliance,
)


@click.group(name="compliance")
def compliance_group():
    """Manage compliance tags for vault secrets."""


@compliance_group.command(name="tag")
@click.argument("key")
@click.argument("standard")
@click.argument("control_id")
@click.option("--note", default="", help="Optional note.")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
def tag_cmd(key, standard, control_id, note, vault):
    """Tag KEY as compliant with STANDARD / CONTROL_ID."""
    try:
        entry = tag_compliant(vault, key, standard, control_id, note=note)
        click.echo(f"Tagged '{key}' [{entry['standard']} / {entry['control_id']}]")
    except ComplianceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@compliance_group.command(name="remove")
@click.argument("key")
@click.argument("standard")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
def remove_cmd(key, standard, vault):
    """Remove compliance entries for KEY under STANDARD."""
    try:
        remove_compliance(vault, key, standard)
        click.echo(f"Removed '{standard}' compliance from '{key}'")
    except ComplianceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@compliance_group.command(name="get")
@click.argument("key")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
def get_cmd(key, vault):
    """Show compliance entries for KEY."""
    entries = get_compliance(vault, key)
    if not entries:
        click.echo(f"No compliance entries for '{key}'.")
        return
    for e in entries:
        note_part = f"  # {e['note']}" if e["note"] else ""
        click.echo(f"  {e['standard']} / {e['control_id']}{note_part}")


@compliance_group.command(name="list")
@click.option("--vault", required=True, envvar="ENVAULT_PATH", help="Path to vault file.")
def list_cmd(vault):
    """List all compliance tags in the vault."""
    data = list_compliance(vault)
    if not data:
        click.echo("No compliance tags found.")
        return
    for key, entries in sorted(data.items()):
        click.echo(f"{key}:")
        for e in entries:
            note_part = f"  # {e['note']}" if e["note"] else ""
            click.echo(f"  {e['standard']} / {e['control_id']}{note_part}")
