"""Encryption and decryption utilities for envault using Fernet symmetric encryption."""

import os
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


SALT_SIZE = 16
ITERATIONS = 390000


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a password and salt using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def generate_salt() -> bytes:
    """Generate a cryptographically secure random salt."""
    return os.urandom(SALT_SIZE)


def encrypt(plaintext: str, password: str) -> bytes:
    """
    Encrypt plaintext using a password-derived key.
    Returns salt + encrypted data as a single bytes blob.
    """
    salt = generate_salt()
    key = derive_key(password, salt)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(plaintext.encode())
    return salt + encrypted


def decrypt(ciphertext: bytes, password: str) -> str:
    """
    Decrypt ciphertext using a password-derived key.
    Expects salt prepended to the encrypted data.

    Raises:
        ValueError: If the ciphertext is too short to contain a valid salt,
            or if decryption fails due to an incorrect password or corrupted data.
    """
    if len(ciphertext) <= SALT_SIZE:
        raise ValueError(
            f"Ciphertext is too short: expected more than {SALT_SIZE} bytes, "
            f"got {len(ciphertext)}."
        )
    salt = ciphertext[:SALT_SIZE]
    encrypted = ciphertext[SALT_SIZE:]
    key = derive_key(password, salt)
    fernet = Fernet(key)
    try:
        return fernet.decrypt(encrypted).decode()
    except InvalidToken:
        raise ValueError(
            "Decryption failed: incorrect password or corrupted ciphertext."
        )
