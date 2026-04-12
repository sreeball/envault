# Vault Watch

The `watch` feature lets you monitor a vault file for changes and react automatically — printing alerts, firing hooks, or triggering custom scripts.

## CLI Usage

```bash
# Watch the default vault with 1-second polling
envault watch start

# Watch a specific vault file
envault watch start --vault /path/to/vault.db

# Adjust polling interval
envault watch start --interval 0.5

# Stop automatically after 60 seconds
envault watch start --timeout 60

# Fire registered on_change hooks when a change is detected
envault watch start --fire-hooks
```

## Python API

### `watch(vault_path, callback, interval, timeout)`

Polls `vault_path` every `interval` seconds. Calls `callback(path)` whenever the file's modification time changes. Returns the total number of change events.

```python
from pathlib import Path
from envault.watch import watch

def on_change(path):
    print(f"Vault changed: {path}")

watch(Path("vault.db"), on_change, interval=1.0, timeout=60.0)
```

### `watch_once(vault_path, callback, interval, timeout)`

Waits for a **single** change event within `timeout` seconds. Returns `True` if a change was detected, `False` if timed out.

```python
from envault.watch import watch_once

changed = watch_once(Path("vault.db"), on_change, timeout=10.0)
if not changed:
    print("No changes detected within timeout.")
```

### `watch_multi(vault_paths, callback, interval, timeout)`

Watches **multiple** vault files simultaneously. Calls `callback(path)` with the specific file that changed. Returns a dict mapping each path to its change count.

```python
from envault.watch import watch_multi

paths = [Path("vault.db"), Path("secrets.db")]
counts = watch_multi(paths, on_change, interval=1.0, timeout=60.0)
for path, count in counts.items():
    print(f"{path}: {count} change(s) detected")
```

## Hook Integration

Register an `on_change` hook with `envault hooks add` and pass `--fire-hooks` to `watch start`. Every matching hook command will be executed in a shell when a change is detected.

## Errors

`WatchError` is raised if the vault file does not exist when watching begins. When using `watch_multi`, a `WatchError` is raised listing **all** missing paths before polling starts.
