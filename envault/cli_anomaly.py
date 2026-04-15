"""CLI commands for anomaly detection."""
import click
from envault.anomaly import (
    record_anomaly,
    list_anomalies,
    clear_anomalies,
    summary,
    AnomalyError,
)


@click.group("anomaly")
def anomaly_group():
    """Detect and manage anomalies in vault secrets."""


@anomaly_group.command("record")
@click.argument("vault_path")
@click.argument("key")
@click.argument("anomaly_type")
@click.option("--detail", default="", help="Additional detail about the anomaly.")
@click.option(
    "--severity",
    default="medium",
    type=click.Choice(["low", "medium", "high", "critical"]),
    help="Severity level.",
)
def record_cmd(vault_path, key, anomaly_type, detail, severity):
    """Record an anomaly for KEY."""
    try:
        entry = record_anomaly(vault_path, key, anomaly_type, detail=detail, severity=severity)
        click.echo(f"Anomaly recorded: [{entry['severity']}] {entry['type']}")
        if entry["detail"]:
            click.echo(f"  Detail: {entry['detail']}")
    except AnomalyError as exc:
        raise click.ClickException(str(exc))


@anomaly_group.command("list")
@click.argument("vault_path")
@click.argument("key")
def list_cmd(vault_path, key):
    """List all anomalies recorded for KEY."""
    entries = list_anomalies(vault_path, key)
    if not entries:
        click.echo(f"No anomalies recorded for '{key}'.")
        return
    click.echo(f"Anomalies for '{key}':")
    for i, e in enumerate(entries, 1):
        detail = f" — {e['detail']}" if e["detail"] else ""
        click.echo(f"  {i}. [{e['severity']}] {e['type']}{detail}")


@anomaly_group.command("clear")
@click.argument("vault_path")
@click.argument("key")
def clear_cmd(vault_path, key):
    """Clear all anomalies for KEY."""
    removed = clear_anomalies(vault_path, key)
    click.echo(f"Cleared {removed} anomaly(s) for '{key}'.")


@anomaly_group.command("summary")
@click.argument("vault_path")
def summary_cmd(vault_path):
    """Show a summary of all keys with anomalies."""
    data = summary(vault_path)
    if not data:
        click.echo("No anomalies recorded.")
        return
    click.echo("Anomaly summary:")
    for key, count in sorted(data.items()):
        click.echo(f"  {key}: {count} anomaly(s)")
