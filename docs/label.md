# Label Management

Labels let you organize and categorize secrets within a vault using free-form string tags.

## Overview

Each secret key can have one or more labels. Labels are stored in a `.envault_labels.json` file alongside the vault.

## Python API

```python
from envault.label import add_label, remove_label, get_labels, keys_with_label, all_labels

vault = "vault.json"

# Add labels to a key
add_label(vault, "DB_URL", "database")
add_label(vault, "DB_URL", "production")

# Retrieve labels for a key
labels = get_labels(vault, "DB_URL")
# ["database", "production"]

# Find all keys with a specific label
keys = keys_with_label(vault, "production")
# ["DB_URL", ...]

# Remove a label
remove_label(vault, "DB_URL", "production")

# Get the full label map
data = all_labels(vault)
```

## CLI Usage

```bash
# Add a label
envault label add DB_URL database

# Remove a label
envault label remove DB_URL database

# List labels for a key
envault label list DB_URL

# Find keys by label
envault label find production

# Show all labels
envault label all
```

## Errors

- `LabelError` is raised if you try to add an empty label or remove a label that does not exist on the key.

## Storage

Labels are persisted in `.envault_labels.json` in the same directory as the vault file:

```json
{
  "DB_URL": ["database", "production"],
  "API_KEY": ["external", "sensitive"]
}
```
