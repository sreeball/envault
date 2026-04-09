# envault

Securely manage and sync environment variables across multiple projects with encryption.

## Installation

```bash
pip install envault
```

## Usage

Initialize a new vault in your project directory, add secrets, and sync them across environments.

```python
from envault import Vault

# Create or open a vault
vault = Vault("my-project", key="your-secret-key")

# Store environment variables
vault.set("DATABASE_URL", "postgres://user:pass@localhost/db")
vault.set("API_KEY", "sk-abc123")

# Load variables into the environment
vault.load()

# Sync vault to another environment
vault.sync(target="production")
```

Or use the CLI:

```bash
# Initialize a new vault
envault init my-project

# Add a secret
envault set API_KEY=sk-abc123

# Load secrets into your shell session
eval $(envault export)
```

## Features

- AES-256 encryption for all stored secrets
- CLI and Python API support
- Multi-project and multi-environment syncing
- `.envault` file format compatible with `.gitignore`

## License

MIT © [envault contributors](LICENSE)