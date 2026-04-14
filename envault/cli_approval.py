"""CLI commands for managing approval requests."""

import click
from envault.approval import (
    ApprovalError,
    request_approval,
    resolve_approval,
    list_approvals,
    get_approval,
)


@click.group("approval")
def approval_group():
    """Manage approval requests for sensitive operations."""


@approval_group.command("request")
@click.argument("key")
@click.argument("operation")
@click.option("--requester", required=True, help="Identity of the requester.")
@click.option("--reason", default="", help="Reason for the request.")
@click.pass_context
def request_cmd(ctx, key, operation, requester, reason):
    """Submit an approval request for KEY and OPERATION."""
    vault_path = ctx.obj["vault_path"]
    try:
        entry = request_approval(vault_path, key, operation, requester, reason=reason)
        click.echo(f"Approval requested. Token: {entry['token']}")
    except ApprovalError as exc:
        raise click.ClickException(str(exc))


@approval_group.command("approve")
@click.argument("token")
@click.option("--resolver", required=True, help="Identity of the approver.")
@click.pass_context
def approve_cmd(ctx, token, resolver):
    """Approve a pending request identified by TOKEN."""
    vault_path = ctx.obj["vault_path"]
    try:
        entry = resolve_approval(vault_path, token, True, resolver)
        click.echo(f"Approved '{entry['key']}' ({entry['operation']}) by {resolver}.")
    except ApprovalError as exc:
        raise click.ClickException(str(exc))


@approval_group.command("reject")
@click.argument("token")
@click.option("--resolver", required=True, help="Identity of the rejector.")
@click.pass_context
def reject_cmd(ctx, token, resolver):
    """Reject a pending request identified by TOKEN."""
    vault_path = ctx.obj["vault_path"]
    try:
        entry = resolve_approval(vault_path, token, False, resolver)
        click.echo(f"Rejected '{entry['key']}' ({entry['operation']}) by {resolver}.")
    except ApprovalError as exc:
        raise click.ClickException(str(exc))


@approval_group.command("list")
@click.option(
    "--status",
    type=click.Choice(["pending", "approved", "rejected"]),
    default=None,
    help="Filter by status.",
)
@click.pass_context
def list_cmd(ctx, status):
    """List approval requests."""
    vault_path = ctx.obj["vault_path"]
    entries = list_approvals(vault_path, status=status)
    if not entries:
        click.echo("No approval requests found.")
        return
    for e in entries:
        click.echo(
            f"[{e['status'].upper()}] {e['token'][:8]}... "
            f"key={e['key']} op={e['operation']} by={e['requester']}"
        )


@approval_group.command("show")
@click.argument("token")
@click.pass_context
def show_cmd(ctx, token):
    """Show details of an approval request by TOKEN."""
    vault_path = ctx.obj["vault_path"]
    try:
        entry = get_approval(vault_path, token)
        for k, v in entry.items():
            click.echo(f"{k}: {v}")
    except ApprovalError as exc:
        raise click.ClickException(str(exc))
