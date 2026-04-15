# Secret Classification

envault supports assigning **classification levels** to individual secret keys,
allowing teams to enforce information-security policies alongside their
encrypted vault.

## Levels

From least to most sensitive:

| Level | Description |
|------------|---------------------------------------------|
| `public` | Safe to share externally |
| `internal` | Internal use only |
| `confidential` | Restricted to specific teams |
| `restricted` | High-sensitivity; limited distribution |
| `top-secret` | Highest sensitivity; need-to-know basis |

## CLI Usage

### Classify a key

```bash
envault classification set API_KEY confidential --reason "Third-party API"
```

### View a key's classification

```bash
envault classification get API_KEY
```

Output:

```
Level : confidential
Reason: Third-party API
```

### Remove a classification

```bash
envault classification remove API_KEY
```

### List all classified keys

```bash
envault classification list
```

### Filter by level

```bash
envault classification list --level restricted
```

## Python API

```python
from envault.classification import classify, get_classification, list_by_level

# Assign a level
classify("vault.db", "DB_PASSWORD", "restricted", reason="PCI DSS")

# Query
entry = get_classification("vault.db", "DB_PASSWORD")
print(entry["level"])   # restricted

# Find all restricted keys
keys = list_by_level("vault.db", "restricted")
```

## Storage

Classification metadata is stored in `.envault_classification.json` alongside
the vault file. This file is **not** encrypted — it contains only key names
and levels, never secret values.

## Integration tips

- Combine with `envault access` to enforce read permissions on `restricted`
  and `top-secret` keys.
- Use `envault lint` rules to warn when a key has no classification.
- Hook into CI to block deployment of `top-secret` keys to non-production
  environments.
