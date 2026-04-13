# Secret Strength Scoring

Envault can analyse the strength of your stored secrets and assign each one a
numerical score (0–100) and a letter grade (A–F).

## How scoring works

Each secret value is evaluated against the following criteria:

| Criterion | Penalty |
|---|---|
| Length < 8 characters | −40 |
| Length 8–15 characters | −15 |
| No uppercase letters | −10 |
| No digits | −10 |
| No special characters | −10 |
| Repeated character runs (4+) | −10 |

The resulting score maps to a grade:

| Score | Grade |
|---|---|
| 90–100 | A |
| 75–89 | B |
| 60–74 | C |
| 40–59 | D |
| 0–39 | F |

## Python API

```python
from envault.scoring import score_value, score_vault, summary

# Score a single value
result = score_value("DB_PASSWORD", "s3cr3t!")
print(result.score, result.grade, result.issues)

# Score every secret in a vault
results = score_vault(Path("vault.json"), "my-master-password")
print(summary(results))
```

## CLI

### Score all secrets

```bash
envault score all vault.json --password <password>
```

Optionally enforce a minimum grade — the command exits non-zero if any key
fails to meet the threshold:

```bash
envault score all vault.json --password <password> --min-grade B
```

### Score a single value

Useful for quick checks before storing a secret:

```bash
envault score key MY_SECRET "C0mpl3x!P@ssw0rd"
```

Example output:

```
[A] MY_SECRET — score=100/100 (OK)
```

## ScoreResult object

| Attribute | Type | Description |
|---|---|---|
| `key` | `str` | The secret key name |
| `score` | `int` | Numeric score 0–100 |
| `grade` | `str` | Letter grade A–F |
| `issues` | `list[str]` | List of detected weaknesses |
| `ok` | `bool` | `True` when score ≥ 60 |
