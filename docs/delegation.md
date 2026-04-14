# Delegation

Delegation lets you grant **scoped, time-limited** access to specific vault keys
without sharing your master password.

## Concepts

| Term | Meaning |
|---|---|
| **delegator** | The vault owner who creates the token |
| **delegatee** | The identity (user, service) receiving access |
| **token** | A UUID4 string used to prove the delegation |
| **keys** | The subset of vault keys covered by this delegation |
| **TTL** | Lifetime of the token in seconds (default 3600) |

## Python API

```python
from envault.delegation import (
    create_delegation,
    revoke_delegation,
    check_delegation,
    list_delegations,
)

# Grant alice access to DB_URL for one hour
entry = create_delegation(
    vault_path="prod.vault",
    delegatee="alice",
    keys=["DB_URL", "REDIS_URL"],
    ttl_seconds=3600,
    note="CI pipeline job #42",
)
print(entry["token"])  # share this with alice

# Verify access at request time
allowed = check_delegation("prod.vault", token, "DB_URL")  # True / False

# Revoke early
revoke_delegation("prod.vault", token)

# Inspect all active delegations
for d in list_delegations("prod.vault"):
    print(d["delegatee"], d["expires_at"])
```

## CLI

```bash
# Create a delegation (prompts for vault password)
envault delegation create --vault prod.vault alice DB_URL REDIS_URL --ttl 1800

# Check access
envault delegation check --vault prod.vault <token> DB_URL

# Revoke
envault delegation revoke --vault prod.vault <token>

# List all
envault delegation list --vault prod.vault
```

## Storage

Delegations are persisted in `.envault_delegations.json` next to the vault
file.  Each entry stores:

```json
{
  "<uuid>": {
    "token": "<uuid>",
    "delegatee": "alice",
    "keys": ["DB_URL"],
    "created_at": "2024-01-01T00:00:00+00:00",
    "expires_at": "2024-01-01T01:00:00+00:00",
    "note": ""
  }
}
```

## Security Notes

- Tokens are UUID4 — not cryptographically signed.  Treat them as secrets.
- Expired tokens are rejected by `check_delegation` but remain on disk until
  explicitly revoked or the file is cleaned up.
- Delegation does **not** re-encrypt values; the delegatee still needs the
  vault password to decrypt.  Use this feature alongside `access.py` for
  full RBAC enforcement.
