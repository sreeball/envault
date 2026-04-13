# Rate Limiting

Envault supports per-operation rate limiting to protect vaults from excessive
access. Limits are stored alongside the vault in a `.envault_rate_limits.json`
file.

## Concepts

- **Operation**: A named action such as `get`, `set`, or `delete`.
- **max_calls**: Maximum number of calls allowed within the time window.
- **window_seconds**: The rolling time window (in seconds) for counting calls.

Calls older than `window_seconds` are automatically discarded when the limit is
checked, so the window is always rolling.

## Python API

```python
from pathlib import Path
from envault.rate_limit import set_limit, check_and_record, remove_limit, list_limits

vault = Path("my_vault.db")

# Allow at most 10 `get` calls per minute
set_limit(vault, "get", max_calls=10, window_seconds=60)

# Record a call and check whether it is within the limit
result = check_and_record(vault, "get")
print(result["remaining"])  # calls remaining in the current window

# Remove a limit
remove_limit(vault, "get")

# List all limits (without internal call history)
print(list_limits(vault))
```

A `RateLimitError` is raised when:
- A call exceeds the configured limit.
- `max_calls` or `window_seconds` is not a positive integer.
- Attempting to remove a limit that does not exist.

## CLI

```
# Configure a limit
envault rate-limit set <vault> <operation> <max_calls> <window_seconds>

# Remove a limit
envault rate-limit remove <vault> <operation>

# List all limits
envault rate-limit list <vault>

# Test / record a call
envault rate-limit check <vault> <operation>
```

### Examples

```bash
# Allow 20 `get` calls per 60 seconds
envault rate-limit set ./prod.db get 20 60

# List configured limits
envault rate-limit list ./prod.db

# Remove the `get` limit
envault rate-limit remove ./prod.db get
```
