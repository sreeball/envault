"""Tests for envault.crypto encryption/decryption utilities."""

import pytest
from envault.crypto import encrypt, decrypt, derive_key, generate_salt, SALT_SIZE


class TestGenerateSalt:
    def test_returns_bytes(self):
        salt = generate_salt()
        assert isinstance(salt, bytes)

    def test_correct_length(self):
        salt = generate_salt()
        assert len(salt) == SALT_SIZE

    def test_unique_salts(self):
        assert generate_salt() != generate_salt()


class TestDeriveKey:
    def test_returns_bytes(self):
        salt = generate_salt()
        key = derive_key("password", salt)
        assert isinstance(key, bytes)

    def test_deterministic(self):
        salt = generate_salt()
        key1 = derive_key("password", salt)
        key2 = derive_key("password", salt)
        assert key1 == key2

    def test_different_passwords_yield_different_keys(self):
        salt = generate_salt()
        assert derive_key("password1", salt) != derive_key("password2", salt)

    def test_different_salts_yield_different_keys(self):
        assert derive_key("password", generate_salt()) != derive_key("password", generate_salt())


class TestEncryptDecrypt:
    def test_roundtrip(self):
        secret = "MY_SECRET=super_secret_value"
        password = "correct-horse-battery-staple"
        ciphertext = encrypt(secret, password)
        assert decrypt(ciphertext, password) == secret

    def test_ciphertext_is_bytes(self):
        ciphertext = encrypt("value", "password")
        assert isinstance(ciphertext, bytes)

    def test_ciphertext_differs_from_plaintext(self):
        plaintext = "API_KEY=12345"
        ciphertext = encrypt(plaintext, "password")
        assert plaintext.encode() not in ciphertext

    def test_wrong_password_raises(self):
        ciphertext = encrypt("secret", "correct_password")
        with pytest.raises(Exception):
            decrypt(ciphertext, "wrong_password")

    def test_encrypt_same_input_produces_different_ciphertext(self):
        """Each encryption should produce unique output due to random salt."""
        ct1 = encrypt("same_value", "same_password")
        ct2 = encrypt("same_value", "same_password")
        assert ct1 != ct2

    def test_salt_prepended_to_ciphertext(self):
        ciphertext = encrypt("value", "password")
        assert len(ciphertext) > SALT_SIZE
