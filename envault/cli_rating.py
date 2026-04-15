"""CLI commands for the rating feature."""

import click
from envault.cli import get_vault
from envault.rating import RatingError, rate_key, get_rating, remove_rating, list_ratings


@click.group("rating")
def rating_group() -> None:
    """Manage star ratings for secrets."""


@rating_group.command("set")
@click.argument("vault_path")
@click.argument("key")
@click.argument("stars", type=int)
@click.option("--review", default="", help="Optional text review.")
def set_cmd(vault_path: str, key: str, stars: int, review: str) -> None:
    """Rate a secret KEY with 1-5 STARS."""
    try:
        entry = rate_key(vault_path, key, stars, review)
        click.echo(f"Rated '{key}': {entry['stars']} star(s).")
    except RatingError as exc:
        raise click.ClickException(str(exc))


@rating_group.command("get")
@click.argument("vault_path")
@click.argument("key")
def get_cmd(vault_path: str, key: str) -> None:
    """Show the rating for KEY."""
    try:
        entry = get_rating(vault_path, key)
        review_part = f" — {entry['review']}" if entry["review"] else ""
        click.echo(f"{entry['stars']} star(s){review_part}")
    except RatingError as exc:
        raise click.ClickException(str(exc))


@rating_group.command("remove")
@click.argument("vault_path")
@click.argument("key")
def remove_cmd(vault_path: str, key: str) -> None:
    """Remove the rating for KEY."""
    remove_rating(vault_path, key)
    click.echo(f"Rating for '{key}' removed.")


@rating_group.command("list")
@click.argument("vault_path")
def list_cmd(vault_path: str) -> None:
    """List all ratings, highest first."""
    entries = list_ratings(vault_path)
    if not entries:
        click.echo("No ratings recorded.")
        return
    for e in entries:
        review_part = f" — {e['review']}" if e["review"] else ""
        click.echo(f"{e['key']}: {e['stars']} star(s){review_part}")
