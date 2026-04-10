# Vault Sync

The `sync` feature lets you push and pull encrypted vault contents to/from a
shared file path (e.g. a network drive, a mounted secret volume, or a
version-controlled directory).

> **Security note:** The remote file stores the same encrypted blobs as the
> local vault.  The password never leaves your machine.

## CLI usage

### Push local vault to a remote path

```bash
envault sync push /shared/team-vault.json
```

You will be prompted for your vault password.  All keys are written to the
remote file in their encrypted form.

### Pull keys from a remote path

```bash
# Merge remote keys, keeping existing local values
envault sync pull /shared/team-vault.json

# Overwrite local keys with remote values
envault sync pull /shared/team-vault.json --overwrite
```

### Check sync status

```bash
envault sync status /shared/team-vault.json
```

Outputs three sections:

- **Only local** – keys present locally but not in the remote file.
- **Only remote** – keys present in the remote file but not locally.
- **In sync** – keys present in both.

## Python API

```python
from envault.vault import Vault
from envault.sync import push, pull, status

vault = Vault(".envault", password="secret")

# Push
push(vault, "/shared/team-vault.json")

# Pull (merge)
pull(vault, "/shared/team-vault.json")

# Pull (overwrite)
pull(vault, "/shared/team-vault.json", overwrite=True)

# Status
result = status(vault, "/shared/team-vault.json")
print(result["only_local"])   # list of key names
print(result["only_remote"])  # list of key names
print(result["common"])       # list of key names
```

## Options reference

| Flag | Default | Description |
|------|---------|-------------|
| `--vault` | `.envault` | Path to the local vault file |
| `--password` | *(prompted)* | Vault encryption password |
| `--overwrite` | `False` | (`pull` only) Replace local keys with remote values |
