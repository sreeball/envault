# Quota Guard

The `quota_guard` module provides lightweight enforcement helpers that should be
called **before** any mutation that writes secrets to a vault. It integrates
with the existing `quota` module and raises `QuotaGuardError` when a limit
would be exceeded.

## Functions

### `check_vault_quota(vault_path, adding=1)`

Verifies that adding `adding` new secrets to the vault will not exceed the
configured `max_secrets` quota.

```python
from envault.quota_guard import check_vault_quota, QuotaGuardError

try:
    check_vault_quota(Path("my.vault"), adding=1)
except QuotaGuardError as exc:
    print(f"Blocked: {exc}")
```

If no quota file exists, or `max_secrets` is not set, the call is a no-op.

### `check_key_quota(vault_path, key, adding=1)`

Verifies that writing `adding` times to `key` will not exceed the per-key
`max_writes` quota stored in the quota file under `keys.<key>.max_writes`.

```python
from envault.quota_guard import check_key_quota, QuotaGuardError

try:
    check_key_quota(Path("my.vault"), "API_KEY")
except QuotaGuardError as exc:
    print(f"Blocked: {exc}")
```

## Quota file format

Quota files are written by `envault.quota` and live next to the vault:

```json
{
  "max_secrets": 50,
  "keys": {
    "API_KEY": {"max_writes": 10, "writes": 3},
    "DB_PASS": {"max_writes": 5,  "writes": 5}
  }
}
```

## Integration example

Call both guards inside a custom `safe_set` wrapper:

```python
from pathlib import Path
from envault.vault import Vault
from envault.quota_guard import check_vault_quota, check_key_quota

def safe_set(vault_path: Path, password: str, key: str, value: str) -> None:
    check_vault_quota(vault_path)
    check_key_quota(vault_path, key)
    v = Vault(vault_path, password=password)
    v.set(key, value)
```

## Errors

| Exception | Raised when |
|-----------|-------------|
| `QuotaGuardError` | Any configured quota would be exceeded |
