"""CLI commands for managing vault secret policies."""

import click
from envault.cli import get_vault
from envault.policy import add_policy, remove_policy, list_policies, enforce, PolicyError


@click.group("policy")
def policy_group():
    """Manage secret policies (required keys, value patterns)."""


@policy_group.command("add")
@click.argument("key")
@click.option("--required", is_flag=True, default=False, help="Mark key as required.")
@click.option("--pattern", default=None, help="Regex pattern the value must match.")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True)
def add_cmd(key, required, pattern, vault_path):
    """Add or update a policy for KEY."""
    try:
        entry = add_policy(vault_path, key, required=required, pattern=pattern)
        click.echo(f"Policy set for '{key}'.")
        if entry.get("required"):
            click.echo("  required: yes")
        if entry.get("pattern"):
            click.echo(f"  pattern:  {entry['pattern']}")
    except PolicyError as exc:
        raise click.ClickException(str(exc))


@policy_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True)
def remove_cmd(key, vault_path):
    """Remove the policy for KEY."""
    try:
        remove_policy(vault_path, key)
        click.echo(f"Policy for '{key}' removed.")
    except PolicyError as exc:
        raise click.ClickException(str(exc))


@policy_group.command("list")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True)
def list_cmd(vault_path):
    """List all registered policies."""
    policies = list_policies(vault_path)
    if not policies:
        click.echo("No policies defined.")
        return
    for key, rule in policies.items():
        req = "required" if rule.get("required") else "optional"
        pat = f"  pattern={rule['pattern']}" if rule.get("pattern") else ""
        click.echo(f"{key}  [{req}]{pat}")


@policy_group.command("check")
@click.option("--vault", "vault_path", envvar="ENVAULT_VAULT", required=True)
@click.option("--password", prompt=True, hide_input=True)
def check_cmd(vault_path, password):
    """Enforce policies against the current vault contents."""
    vault = get_vault(vault_path, password)
    secrets = {k: vault.get(k, password) for k in vault.keys()}
    violations = enforce(vault_path, secrets)
    if not violations:
        click.echo("All policies satisfied.")
    else:
        for v in violations:
            click.echo(f"VIOLATION: {v}")
        raise click.ClickException(f"{len(violations)} policy violation(s) found.")
