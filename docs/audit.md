# Audit Logging

envault records every mutating vault operation to an append-only JSON audit log.
This lets you track *who* changed *what* and *when* across a team.

## Log location

By default the log lives next to your vault file:

```
.envault.json       # vault data
.envault.audit.json # audit log
```

You can customise the path by passing `--audit-log <path>` to any CLI command.

## Entry format

Each entry is a JSON object:

```json
{
  "version": 1,
  "timestamp": "2024-06-01T12:34:56.789012+00:00",
  "action": "set",
  "key": "DATABASE_URL",
  "actor": "alice"
}
```

| Field       | Description                                      |
|-------------|--------------------------------------------------|
| `version`   | Schema version (currently `1`)                   |
| `timestamp` | UTC ISO-8601 timestamp of the operation          |
| `action`    | One of `set`, `get`, `delete`, `push`, `pull`    |
| `key`       | The environment variable name that was touched   |
| `actor`     | Username (`$USER`) or value passed via `--actor` |

## Programmatic usage

```python
from pathlib import Path
from envault.audit import record, get_log, clear_log

log = Path(".envault.audit.json")

# Record an action
record(log, action="set", key="API_KEY", actor="bob")

# Read all entries
for entry in get_log(log):
    print(entry["timestamp"], entry["actor"], entry["action"], entry["key"])

# Purge the log (returns number of deleted entries)
n = clear_log(log)
print(f"Removed {n} entries")
```

## CLI commands

```bash
# Show the audit log for the current vault
envault audit list

# Clear the audit log
envault audit clear
```

## Security notes

- The audit log is **not encrypted**. Do not store secrets as key names.
- For tamper-evident logging, store the log file in a version-controlled
  repository or forward entries to a centralised logging service.
