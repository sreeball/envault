import click
from envault.intensity import (
    set_intensity,
    get_intensity,
    remove_intensity,
    list_intensity,
    IntensityError,
)


@click.group("intensity")
def intensity_group():
    """Manage key intensity levels."""


@intensity_group.command("set")
@click.argument("vault_path")
@click.argument("key")
@click.argument("level")
@click.option("--note", default="", help="Optional note.")
def set_cmd(vault_path, key, level, note):
    """Set the intensity level for a key."""
    try:
        entry = set_intensity(vault_path, key, level, note)
        click.echo(f"Intensity for '{key}' set to '{entry['level']}'.")
    except IntensityError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@intensity_group.command("get")
@click.argument("vault_path")
@click.argument("key")
def get_cmd(vault_path, key):
    """Get the intensity level for a key."""
    try:
        entry = get_intensity(vault_path, key)
        click.echo(f"{key}: {entry['level']}" + (f" ({entry['note']})" if entry["note"] else ""))
    except IntensityError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@intensity_group.command("remove")
@click.argument("vault_path")
@click.argument("key")
def remove_cmd(vault_path, key):
    """Remove intensity setting for a key."""
    try:
        remove_intensity(vault_path, key)
        click.echo(f"Intensity removed for '{key}'.")
    except IntensityError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@intensity_group.command("list")
@click.argument("vault_path")
def list_cmd(vault_path):
    """List all intensity settings."""
    data = list_intensity(vault_path)
    if not data:
        click.echo("No intensity settings found.")
        return
    for key, entry in data.items():
        note_part = f" ({entry['note']})" if entry["note"] else ""
        click.echo(f"{key}: {entry['level']}{note_part}")
