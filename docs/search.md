# Secret Search

envault provides flexible search functionality to locate secrets within a vault
by key name or value, using either glob patterns or regular expressions.

## Python API

### `search(vault, password, pattern, *, regex=False, keys_only=False)`

Decrypts and returns all secrets whose key **or** value matches `pattern`.

| Parameter   | Type   | Description                                          |
|-------------|--------|------------------------------------------------------|
| `vault`     | Vault  | The vault instance to search.                        |
| `password`  | str    | Master password for decryption.                      |
| `pattern`   | str    | Glob pattern or regular expression.                  |
| `regex`     | bool   | Interpret `pattern` as a regex (default: `False`).   |
| `keys_only` | bool   | Skip value matching (default: `False`).              |

Returns a `dict[str, str]` mapping matched keys to their plaintext values.

```python
from envault.vault import Vault
from envault.search import search

vault = Vault("vault.json")
results = search(vault, "my-password", "DB_*")
for key, value in results.items():
    print(f"{key}={value}")
```

### `list_keys_matching(vault, pattern, *, regex=False)`

Returns a list of keys matching `pattern` **without** decrypting any values.
Useful for key discovery when you do not need the secret values.

```python
from envault.search import list_keys_matching

keys = list_keys_matching(vault, "API_*")
print(keys)  # ['API_KEY', 'API_SECRET']
```

## CLI

### List matching keys (no password required)

```bash
envault search keys "DB_*"
envault search keys "^DB" --regex
```

### Search secrets (password required)

```bash
# Glob pattern, table output (default)
envault search secrets "API_*"

# Regular expression
envault search secrets "^DB_" --regex

# Only match keys, not values
envault search secrets "HOST" --keys-only

# Output as JSON
envault search secrets "*" --format json

# Output keys only
envault search secrets "DB_*" --format keys
```

## Error Handling

- `SearchError` is raised when the pattern is empty or an invalid regex is supplied.
- The CLI converts `SearchError` into a non-zero exit code with an error message.
