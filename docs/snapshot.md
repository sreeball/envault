# Vault Snapshots

Snapshots let you save a point-in-time copy of all secrets in a vault and
restore them later. This is useful before bulk edits, deployments, or key
rotations.

## How it works

When you create a snapshot, **envault** decrypts every secret in the vault and
writes them as plain JSON inside a hidden `.envault_snapshots/` directory next
to the vault file. Snapshots are **not** encrypted — keep the snapshots
directory out of version control (it is already listed in `.gitignore`).

## CLI usage

### Create a snapshot

```bash
envault snapshot create --vault path/to/vault.db
# With an optional label
envault snapshot create --vault path/to/vault.db --label before-deploy
```

Outputs the path to the new snapshot file and the number of secrets captured.

### List snapshots

```bash
envault snapshot list --vault path/to/vault.db
```

Prints each snapshot with its timestamp, label (if any), secret count, and
file path, ordered newest first.

### Restore a snapshot

```bash
envault snapshot restore /path/to/snapshot.json --vault path/to/vault.db
```

Overwrites the current vault secrets with those stored in the snapshot. Secrets
not present in the snapshot are left untouched.

### Delete a snapshot

```bash
envault snapshot delete /path/to/snapshot.json --vault path/to/vault.db
```

Prompts for confirmation before removing the file.

## Python API

```python
from envault.snapshot import create_snapshot, list_snapshots, restore_snapshot, delete_snapshot

# Save current state
meta = create_snapshot("vault.db", password="s3cr3t", label="v1.2")
print(meta)  # {'snapshot': '...', 'timestamp': '...', 'label': 'v1.2', 'count': 5}

# List all snapshots
for snap in list_snapshots("vault.db"):
    print(snap["timestamp"], snap["label"], snap["count"])

# Restore
restore_snapshot("vault.db", password="s3cr3t", snapshot_file=meta["snapshot"])

# Delete
delete_snapshot("vault.db", snapshot_file=meta["snapshot"])
```

## Errors

| Exception | Cause |
|-----------|-------|
| `SnapshotError` | Snapshot file missing or corrupt |
