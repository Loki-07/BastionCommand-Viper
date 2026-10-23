"""Whole-file envelope encryption for a single database file.

This encrypts an entire file (a SQLite database) as one opaque blob using
Fernet (AES-128-CBC + HMAC-SHA256, from the `cryptography` package), with a
passphrase-derived key (PBKDF2-HMAC-SHA256). There are no compiled/native
dependencies — everything here is pure Python plus `cryptography`'s prebuilt
wheels, which are widely available (including Windows).

This module only knows how to encrypt/decrypt bytes into a container file. It
has no opinion about *when* to do that or where a decrypted working copy
should live while the app is running — see `security.encrypted_database` for
that lifecycle.

Container format (all integers big-endian):
    MAGIC (8 bytes)        b"VIPRENC1"
    salt_length (1 byte)
    kdf_iterations (4 bytes)
    salt (salt_length bytes)
    fernet_token (remaining bytes)

The salt and iteration count are not secret and are safe to store alongside
the ciphertext.
"""

from __future__ import annotations

import base64
import os
import struct
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

MAGIC = b"VIPRENC1"
SALT_LENGTH = 16
# OWASP's 2023 minimum recommendation for PBKDF2-HMAC-SHA256.
DEFAULT_KDF_ITERATIONS = 600_000

_HEADER_STRUCT = struct.Struct(">BI")  # salt_length, kdf_iterations


class InvalidPassphraseError(Exception):
    """Raised when a passphrase fails to decrypt/authenticate a container."""


def is_encrypted_container(path: Path) -> bool:
    """Return True if `path` exists and looks like a Viper encrypted container."""
    try:
        with open(path, "rb") as handle:
            return handle.read(len(MAGIC)) == MAGIC
    except OSError:
        return False


def _derive_key(passphrase: str, salt: bytes, iterations: int) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def encrypt_bytes(plaintext: bytes, passphrase: str, *, iterations: int = DEFAULT_KDF_ITERATIONS) -> bytes:
    """Encrypt `plaintext` into a self-contained container (header + ciphertext)."""
    salt = os.urandom(SALT_LENGTH)
    key = _derive_key(passphrase, salt, iterations)
    token = Fernet(key).encrypt(plaintext)
    header = MAGIC + _HEADER_STRUCT.pack(SALT_LENGTH, iterations) + salt
    return header + token


def decrypt_bytes(container: bytes, passphrase: str) -> bytes:
    """Return the decrypted plaintext, or raise InvalidPassphraseError/ValueError."""
    if container[: len(MAGIC)] != MAGIC:
        raise ValueError("Not a Viper encrypted database container.")

    offset = len(MAGIC)
    salt_length, iterations = _HEADER_STRUCT.unpack(container[offset : offset + _HEADER_STRUCT.size])
    offset += _HEADER_STRUCT.size
    salt = container[offset : offset + salt_length]
    offset += salt_length
    token = container[offset:]

    key = _derive_key(passphrase, salt, iterations)
    try:
        return Fernet(key).decrypt(token)
    except InvalidToken as exc:
        raise InvalidPassphraseError("Incorrect passphrase, or the database file is corrupted.") from exc


def encrypt_file(plaintext_path: Path, encrypted_path: Path, passphrase: str) -> None:
    """Encrypt `plaintext_path` into a container written atomically to `encrypted_path`."""
    container = encrypt_bytes(plaintext_path.read_bytes(), passphrase)
    temp_path = encrypted_path.with_name(encrypted_path.name + ".tmp")
    temp_path.write_bytes(container)
    os.replace(temp_path, encrypted_path)


def decrypt_file(encrypted_path: Path, passphrase: str) -> bytes:
    """Return the decrypted plaintext bytes of the container at `encrypted_path`."""
    return decrypt_bytes(encrypted_path.read_bytes(), passphrase)
