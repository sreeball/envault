# Cascade Resolution

Cascade resolution lets you merge secrets from **multiple vaults** in a defined priority order. The vault listed first always wins when two vaults define the same key.

## Use cases

- Override production defaults with per-developer local secrets.
- Layer shared team secrets beneath project-specific values.
- Provide fallback values from a base vault when a feature vault is sparse.

## API

### `resolve(vault_paths, password, *, keys=None) -> dict`

Merge all vaults and return a plain-text `{key: value}` dictionary.

| Parameter | Type | Description |
|-----------|------|-------------|
| `vault_paths` | `list[Path]` | Ordered paths; index 0 has highest priority. |
| `password` | `str` | Shared decryption password for every vault. |
| `keys` | `list[str] \| None` | Optional allowlist — only these keys are returned. |

Raises `CascadeError` if any vault is missing or cannot be decrypted.

### `sources(vault_paths, password, key) -> Path | None`

Return the highest-priority vault path that contains `key`, or `None`.

### `audit(vault_paths, password) -> dict[str, Path]`

Return a mapping of every key across all vaults to the vault path that would
win during resolution. Useful for inspecting which vault "owns" each secret
without performing a full `resolve`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `vault_paths` | `list[Path]` | Ordered paths; index 0 has highest priority. |
| `password` | `str` | Shared decryption password for every vault. |

Raises `CascadeError` if any vault is missing or cannot be decrypted.

## Example

```python
from pathlib import Path
from envault.cascade import resolve, sources, audit

vaults = [
    Path("local.vault"),   # developer overrides
    Path("team.vault"),    # shared team defaults
    Path("base.vault"),    # project base values
]

secrets = resolve(vaults, password="s3cr3t")
print(secrets["DATABASE_URL"])

origin = sources(vaults, password="s3cr3t", key="DATABASE_URL")
print(f"DATABASE_URL comes from {origin}")

# See which vault owns every key
ownership = audit(vaults, password="s3cr3t")
for key, vault_path in ownership.items():
    print(f"{key:30s} → {vault_path}")
```

## Notes

- All vaults must be encrypted with the **same password**.
- Vaults that do not exist on disk raise `CascadeError` during `resolve`, but are silently skipped by `sources`.
- The `keys` filter is applied *after* merging, so priority rules still apply across all vaults.
