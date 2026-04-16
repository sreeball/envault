"""CLI commands for risk assessment."""
import click
from .cli import get_vault
from .risk import set_risk, get_risk, remove_risk, list_risk, RiskError, VALID_LEVELS


@click.group("risk")
def risk_group():
    """Manage risk levels for secrets."""


@risk_group.command("set")
@click.argument("key")
@click.argument("level", type=click.Choice(VALID_LEVELS))
@click.option("--reason", default="", help="Reason for this risk level.")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
def set_cmd(key, level, reason, vault_path):
    """Set the risk level for a secret KEY."""
    try:
        entry = set_risk(vault_path, key, level, reason)
        click.echo(f"Risk level for '{key}' set to '{entry['level']}'.")
    except RiskError as e:
        raise click.ClickException(str(e))


@risk_group.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
def get_cmd(key, vault_path):
    """Get the risk level for a secret KEY."""
    entry = get_risk(vault_path, key)
    if entry is None:
        click.echo(f"No risk assessment for '{key}'.")
    else:
        click.echo(f"{key}: {entry['level']}" + (f" ({entry['reason']})" if entry["reason"] else ""))


@risk_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
def remove_cmd(key, vault_path):
    """Remove the risk assessment for KEY."""
    removed = remove_risk(vault_path, key)
    if removed:
        click.echo(f"Risk assessment for '{key}' removed.")
    else:
        click.echo(f"No risk assessment found for '{key}'.")


@risk_group.command("list")
@click.option("--vault", "vault_path", default="vault.env", show_default=True)
def list_cmd(vault_path):
    """List all risk assessments."""
    data = list_risk(vault_path)
    if not data:
        click.echo("No risk assessments recorded.")
        return
    for key, entry in data.items():
        line = f"{key}: {entry['level']}"
        if entry.get("reason"):
            line += f" — {entry['reason']}"
        click.echo(line)
