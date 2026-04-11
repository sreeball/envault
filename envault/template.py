"""Template rendering: substitute vault secrets into template strings."""

import re
from typing import Optional

from envault.vault import Vault

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class TemplateError(Exception):
    """Raised when template rendering fails."""


def render_string(
    template: str,
    vault_path: str,
    password: str,
    *,
    strict: bool = True,
) -> str:
    """Replace ``{{ KEY }}`` placeholders with decrypted vault values.

    Parameters
    ----------
    template:
        The template string containing ``{{ KEY }}`` placeholders.
    vault_path:
        Path to the vault file.
    password:
        Master password used to decrypt secrets.
    strict:
        When *True* (default) raise :class:`TemplateError` for any
        placeholder whose key is not present in the vault.  When *False*
        leave unresolved placeholders unchanged.

    Returns
    -------
    str
        The rendered string with secrets substituted in.
    """
    vault = Vault(vault_path, password)

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        try:
            return vault.get(key)
        except KeyError:
            if strict:
                raise TemplateError(
                    f"Key '{key}' not found in vault '{vault_path}'"
                ) from None
            return match.group(0)

    return _PLACEHOLDER_RE.sub(_replace, template)


def render_file(
    template_path: str,
    vault_path: str,
    password: str,
    output_path: Optional[str] = None,
    *,
    strict: bool = True,
) -> str:
    """Read *template_path*, render it, and optionally write to *output_path*.

    Returns the rendered content regardless of whether it was written to disk.
    """
    with open(template_path, "r", encoding="utf-8") as fh:
        template = fh.read()

    rendered = render_string(template, vault_path, password, strict=strict)

    if output_path is not None:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(rendered)

    return rendered
