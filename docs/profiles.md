# Profiles

Profiles let you group related secrets under a named label (e.g. `dev`, `staging`, `prod`). A single vault can hold many profiles, and any key can belong to multiple profiles.

## Overview

| Concept | Description |
|---------|-------------|
| **Profile** | A named collection of vault-key references |
| **Key assignment** | Linking an existing vault key to a profile |
| **Profile secrets** | Decrypted view of all keys in a profile |

Profile metadata is stored alongside the vault file as `<vault>.profiles.json`. The file is **not** encrypted — it contains only key names, never values.

## Python API

```python
from pathlib import Path
from envault.profiles import (
    create_profile, assign_key, remove_key,
    list_profiles, get_profile_secrets, delete_profile,
)

vault_path = Path("my.vault.json")

# Create profiles
create_profile(vault_path, "dev")
create_profile(vault_path, "prod")

# Assign keys
assign_key(vault_path, "dev", "DB_URL")
assign_key(vault_path, "dev", "DEBUG")
assign_key(vault_path, "prod", "DB_URL")
assign_key(vault_path, "prod", "API_KEY")

# List all profiles
print(list_profiles(vault_path))  # ['dev', 'prod']

# Retrieve decrypted secrets for a profile
secrets = get_profile_secrets(vault_path, "dev", password="hunter2")
print(secrets)  # {'DB_URL': 'postgres://...', 'DEBUG': 'true'}

# Remove a key from a profile
remove_key(vault_path, "dev", "DEBUG")

# Delete a profile entirely
delete_profile(vault_path, "dev")
```

## Error Handling

All profile functions raise `ProfileError` for invalid operations:

```python
from envault.profiles import ProfileError

try:
    create_profile(vault_path, "dev")  # already exists
except ProfileError as e:
    print(e)  # Profile 'dev' already exists.
```

## Storage Format

`my.vault.profiles.json`:

```json
{
  "dev": ["DB_URL", "DEBUG"],
  "prod": ["DB_URL", "API_KEY"]
}
```

## Notes

- Deleting a vault key does **not** automatically remove it from profiles; `get_profile_secrets` silently skips missing keys.
- Assigning the same key twice is idempotent — no duplicates are stored.
- Profiles do not affect encryption; the vault password is still required to read secret values.
