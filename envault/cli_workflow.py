"""CLI commands for workflow management."""

import click

from envault.cli import get_vault
from envault.workflow import (
    WorkflowError,
    create_workflow,
    delete_workflow,
    get_workflow,
    list_workflows,
)


@click.group("workflow")
def workflow_group():
    """Manage automation workflows."""


@workflow_group.command("create")
@click.argument("name")
@click.argument("steps", nargs=-1, required=True)
@click.option("--description", "-d", default="", help="Human-readable description.")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def create_cmd(name, steps, description, vault_path):
    """Create a named workflow with one or more STEPS."""
    try:
        entry = create_workflow(vault_path, name, list(steps), description=description)
        click.echo(f"Workflow '{entry['name']}' created with {len(entry['steps'])} step(s).")
    except WorkflowError as exc:
        raise click.ClickException(str(exc))


@workflow_group.command("delete")
@click.argument("name")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def delete_cmd(name, vault_path):
    """Delete a workflow by NAME."""
    try:
        delete_workflow(vault_path, name)
        click.echo(f"Workflow '{name}' deleted.")
    except WorkflowError as exc:
        raise click.ClickException(str(exc))


@workflow_group.command("show")
@click.argument("name")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def show_cmd(name, vault_path):
    """Show details of a workflow."""
    try:
        w = get_workflow(vault_path, name)
        click.echo(f"Name: {w['name']}")
        if w["description"]:
            click.echo(f"Description: {w['description']}")
        click.echo("Steps:")
        for i, step in enumerate(w["steps"], 1):
            click.echo(f"  {i}. {step}")
    except WorkflowError as exc:
        raise click.ClickException(str(exc))


@workflow_group.command("list")
@click.option("--vault", "vault_path", default="vault.db", show_default=True)
def list_cmd(vault_path):
    """List all registered workflows."""
    workflows = list_workflows(vault_path)
    if not workflows:
        click.echo("No workflows registered.")
        return
    for w in workflows:
        desc = f" — {w['description']}" if w["description"] else ""
        click.echo(f"{w['name']} ({len(w['steps'])} step(s)){desc}")
