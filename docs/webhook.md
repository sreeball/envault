# Webhook Notifications

envault can POST a JSON payload to one or more HTTP endpoints whenever a vault
event occurs (e.g. a secret is set or deleted).

## Registering a Webhook

```python
from envault.webhook import register_webhook

register_webhook(
    vault_path="myproject/vault.enc",
    name="ci-pipeline",
    url="https://hooks.example.com/envault",
    events=["set", "delete"],
)
```

Webhooks are stored in `.envault_webhooks.json` next to the vault file.

## Supported Events

| Event    | Triggered when …                  |
|----------|-----------------------------------|
| `set`    | A secret is created or updated    |
| `delete` | A secret is removed from the vault|
| `rotate` | The vault password is rotated     |
| `import` | Secrets are bulk-imported         |

## Firing Webhooks Manually

```python
from envault.webhook import fire_webhook

fire_webhook(
    vault_path="myproject/vault.enc",
    event="set",
    payload={"key": "DATABASE_URL"},
)
```

All webhooks whose `events` list includes the given event name will receive a
POST request with a JSON body:

```json
{
  "event": "set",
  "key": "DATABASE_URL"
}
```

## Removing a Webhook

```python
from envault.webhook import unregister_webhook

unregister_webhook(vault_path="myproject/vault.enc", name="ci-pipeline")
```

## Listing Webhooks

```python
from envault.webhook import list_webhooks

for name, cfg in list_webhooks("myproject/vault.enc").items():
    print(name, cfg["url"], cfg["events"])
```

## Error Handling

`WebhookError` is raised when:
- The URL scheme is not `http://` or `https://`.
- No events are specified during registration.
- A network error occurs while delivering the webhook.
