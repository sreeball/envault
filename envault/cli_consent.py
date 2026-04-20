"""CLI commands for consent management."""
import click
from envault.cli import get_vault
from envault.consent import (
    ConsentError,
    grant_consent,
    revoke_consent,
    get_consents,
    has_consent,
    list_all_consents,
)


@click.group("consent")
def consent_group():
    """Manage access consent for vault keys."""


@consent_group.command("grant")
@click.argument("key")
@click.argument("actor")
@click.argument("purpose")
@click.option("--note", default="", help="Optional note (e.g. legal basis).")
@click.option("--vault", "vault_path", envvar="ENVAULT_PATH", required=True)
def grant_cmd(key, actor, purpose, note, vault_path):
    """Grant consent for ACTOR to access KEY for PURPOSE."""
    try:
        entry = grant_consent(vault_path, key, actor, purpose, note=note)
        click.echo(f"Consent granted: {actor} -> {key} [{purpose}]")
        if entry["note"]:
            click.echo(f"  note: {entry['note']}")
    except ConsentError as exc:
        raise click.ClickException(str(exc))


@consent_group.command("revoke")
@click.argument("key")
@click.argument("actor")
@click.option("--purpose", default=None, help="Limit revocation to a specific purpose.")
@click.option("--vault", "vault_path", envvar="ENVAULT_PATH", required=True)
def revoke_cmd(key, actor, purpose, vault_path):
    """Revoke consent for ACTOR on KEY."""
    removed = revoke_consent(vault_path, key, actor, purpose)
    if removed:
        click.echo(f"Revoked {removed} consent entry(ies) for '{actor}' on '{key}'.")
    else:
        click.echo(f"No matching consent entries found for '{actor}' on '{key}'.")


@consent_group.command("check")
@click.argument("key")
@click.argument("actor")
@click.argument("purpose")
@click.option("--vault", "vault_path", envvar="ENVAULT_PATH", required=True)
def check_cmd(key, actor, purpose, vault_path):
    """Check whether ACTOR has consent to access KEY for PURPOSE."""
    if has_consent(vault_path, key, actor, purpose):
        click.echo(f"GRANTED: {actor} has consent for '{key}' [{purpose}]")
    else:
        click.echo(f"DENIED: {actor} does not have consent for '{key}' [{purpose}]")
        raise SystemExit(1)


@consent_group.command("list")
@click.argument("key", required=False)
@click.option("--vault", "vault_path", envvar="ENVAULT_PATH", required=True)
def list_cmd(key, vault_path):
    """List consent entries, optionally filtered to KEY."""
    if key:
        entries = get_consents(vault_path, key)
        if not entries:
            click.echo(f"No consent entries for '{key}'.")
            return
        for e in entries:
            note_part = f" ({e['note']})" if e["note"] else ""
            click.echo(f"  {e['actor']} -> {key} [{e['purpose']}]{note_part}")
    else:
        data = list_all_consents(vault_path)
        if not data:
            click.echo("No consent entries recorded.")
            return
        for k, entries in data.items():
            for e in entries:
                note_part = f" ({e['note']})" if e["note"] else ""
                click.echo(f"  {e['actor']} -> {k} [{e['purpose']}]{note_part}")
