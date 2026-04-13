# Archive

The **archive** module lets you soft-delete secrets from a vault without permanently destroying them.  Archived entries are stored in a sidecar file (`<vault>.archive.json`) and can be restored at any time.

## Functions

### `archive_key(vault_path, key, entry)`

Moves an existing vault entry into the archive store.

| Parameter    | Type            | Description                                  |
|--------------|-----------------|----------------------------------------------|
| `vault_path` | `str`           | Path to the vault file.                      |
| `key`        | `str`           | The secret key to archive.                   |
| `entry`      | `dict`          | The raw vault entry (`salt` + `ciphertext`). |

Raises `ArchiveError` if the key is empty or already archived.

**Returns** `{"key": ..., "archived": True, "entry": ...}`

---

### `restore_key(vault_path, key)`

Removes *key* from the archive and returns its stored entry so the caller can re-insert it into the live vault.

Raises `ArchiveError` if the key is not currently archived.

**Returns** `{"key": ..., "restored": True, "entry": ...}`

---

### `list_archived(vault_path)`

Returns a list of all currently archived key names.

```python
from envault.archive import list_archived

keys = list_archived("/path/to/my.vault")
print(keys)  # ['OLD_API_KEY', 'DEPRECATED_TOKEN']
```

---

### `purge_archived(vault_path, key=None)`

Permanently deletes archived entries.

- If `key` is supplied, only that entry is removed.
- If `key` is `None`, **all** archived entries are deleted.

Returns the number of entries removed.

Raises `ArchiveError` if a specific key is requested but not found in the archive.

---

## Archive file format

The sidecar file is a plain JSON object keyed by secret name:

```json
{
  "OLD_API_KEY": {
    "salt": "<hex>",
    "ciphertext": "<hex>"
  }
}
```

## Example workflow

```python
from envault.vault import Vault
from envault.archive import archive_key, restore_key, list_archived

vault = Vault("prod.vault", password="s3cr3t")

# Soft-delete a key
raw_entry = vault._load_raw()["OLD_TOKEN"]
archive_key("prod.vault", "OLD_TOKEN", raw_entry)
vault.delete("OLD_TOKEN")

# List what is archived
print(list_archived("prod.vault"))  # ['OLD_TOKEN']

# Restore later
result = restore_key("prod.vault", "OLD_TOKEN")
# Re-insert via vault internals if needed
```
