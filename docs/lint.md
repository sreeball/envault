# Vault Linting

envault can inspect your vault for common issues before they cause problems in production.

## What is checked?

| Check | Severity | Description |
|-------|----------|-------------|
| Naming convention | warning | Keys should follow `UPPER_SNAKE_CASE` |
| Weak value | error | Values like `password`, `secret`, `changeme`, or empty strings |
| Short value | warning | Values shorter than 8 characters |
| Expired TTL | error | Secrets whose TTL has already passed |

## Python API

```python
from envault.lint import lint_vault

result = lint_vault("/path/to/vault.json", password="my-master-password")

if not result.ok:
    for issue in result.errors:
        print(f"[ERROR] {issue.key}: {issue.message}")

for issue in result.warnings:
    print(f"[WARN]  {issue.key}: {issue.message}")
```

## Return value

`lint_vault` returns a `LintResult` object:

```
LintResult
  .issues        -> List[LintIssue]
  .errors        -> filtered list of severity='error'
  .warnings      -> filtered list of severity='warning'
  .ok            -> True when no errors are present
```

Each `LintIssue` has:
- `key` — the vault key that triggered the issue
- `severity` — `'error'` or `'warning'`
- `message` — human-readable description

## Exit behaviour

A vault that passes all checks with no errors is considered **clean**. Warnings are
advisory and do not block operations, but errors indicate secrets that should be
rotated or corrected before deployment.
