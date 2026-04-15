# Anomaly Detection

The `anomaly` module lets you record, inspect, and clear anomalous events
observed on vault secrets — for example, unusually short values, unexpected
access bursts, or suspicious patterns detected by an external scanner.

## Python API

```python
from envault.anomaly import record_anomaly, list_anomalies, clear_anomalies, summary

# Record an anomaly for a key
entry = record_anomaly(
    "path/to/vault.enc",
    key="DB_PASSWORD",
    anomaly_type="unusual_length",
    detail="value is only 4 characters",
    severity="high",   # low | medium | high | critical
)

# List anomalies for a specific key
anomalies = list_anomalies("path/to/vault.enc", "DB_PASSWORD")
for a in anomalies:
    print(a["severity"], a["type"], a["detail"])

# Clear anomalies for a key
removed = clear_anomalies("path/to/vault.enc", "DB_PASSWORD")
print(f"Removed {removed} anomaly(s)")

# Summary across all keys
for key, count in summary("path/to/vault.enc").items():
    print(f"{key}: {count} anomaly(s)")
```

## CLI

```bash
# Record an anomaly
envault anomaly record vault.enc DB_PASSWORD unusual_length \
    --detail "only 4 chars" --severity high

# List anomalies for a key
envault anomaly list vault.enc DB_PASSWORD

# Clear anomalies for a key
envault anomaly clear vault.enc DB_PASSWORD

# Show anomaly summary
envault anomaly summary vault.enc
```

## Severity Levels

| Level    | Meaning                                      |
|----------|----------------------------------------------|
| low      | Informational, unlikely to cause issues      |
| medium   | Should be reviewed                           |
| high     | Likely problematic, action recommended       |
| critical | Immediate action required                    |

## Storage

Anomalies are stored alongside the vault in `.envault_anomalies.json`.
This file is **not encrypted** — avoid storing sensitive values in the
`detail` field.
