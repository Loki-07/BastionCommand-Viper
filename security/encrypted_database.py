"""Working-copy lifecycle for encrypted Viper databases.

Fernet (see `security.envelope`) encrypts/decrypts whole files, but SQLite
needs a plain file on disk to open as a live database. This module manages
that plaintext "working copy": decrypt-on-open, re-encrypt-and-shred-on-close,
plus crash recovery if the app didn't close cleanly last time.

Threat model / known trade-off: while the app is running, a plaintext copy of
the database exists on disk (at a non-guessable, per-database path under the
user's local app-data folder). This is weaker than SQLCipher's page-level
in-use encryption, but requires no compiled/native dependency. Treat OS-level
disk encryption (BitLocker/FileVault) as the defense-in-depth baseline this
is layered on top of, not a replacement for it.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from security.envelope import decrypt_file, encrypt_file

_APP_DATA_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
_DECRYPTED_CACHE_ROOT = _APP_DATA_ROOT / "BastionCommand" / "Viper" / "decrypted_cache"


@dataclass
class EncryptionSession:
    """The state needed to re-encrypt a database when the app closes."""

    encrypted_path: Path
    working_copy_path: Path
    passphrase: str


_active_session: EncryptionSession | None = None


def set_active_session(session: EncryptionSession | None) -> None:
    global _active_session
    _active_session = session


def get_active_session() -> EncryptionSession | None:
    return _active_session


def get_working_copy_path(encrypted_path: Path) -> Path:
    """A stable, non-guessable plaintext path for a given encrypted database.

    Stable (not random) so a leftover working copy from an unclean shutdown
    can be found again and recovered on the next launch of the same database.
    """
    digest = hashlib.sha256(os.path.normcase(str(encrypted_path.resolve())).encode("utf-8")).hexdigest()
    return _DECRYPTED_CACHE_ROOT / f"{digest[:32]}.db"


def create_encrypted_database(encrypted_path: Path) -> Path:
    """Return the working-copy path to use for a brand-new encrypted database.

    Does not touch the encrypted path itself — the caller is expected to run
    `init_db()` (or similar) against the returned path, then call
    `encrypt_snapshot()` to persist the first encrypted container.
    """
    working_copy_path = get_working_copy_path(encrypted_path)
    working_copy_path.parent.mkdir(parents=True, exist_ok=True)
    return working_copy_path


def open_encrypted_database(encrypted_path: Path, passphrase: str) -> tuple[Path, bool]:
    """Decrypt `encrypted_path` into a working copy, or recover a leftover one.

    Returns (working_copy_path, recovered). `recovered` is True when a
    leftover working copy from a previous session that didn't close cleanly
    was reused instead of decrypting the on-disk container (the leftover copy
    is strictly as new as, or newer than, the encrypted container).

    Raises `security.envelope.InvalidPassphraseError` on a wrong passphrase,
    even when recovering — the master container is always re-checked against
    the passphrase so a stale working copy can't be used to bypass it.
    """
    working_copy_path = get_working_copy_path(encrypted_path)

    if working_copy_path.exists():
        decrypt_file(encrypted_path, passphrase)  # validates the passphrase; result unused
        return working_copy_path, True

    plaintext = decrypt_file(encrypted_path, passphrase)
    working_copy_path.parent.mkdir(parents=True, exist_ok=True)
    working_copy_path.write_bytes(plaintext)
    return working_copy_path, False


def encrypt_snapshot(encrypted_path: Path, working_copy_path: Path, passphrase: str) -> None:
    """Re-encrypt the working copy into the master container, without deleting it."""
    encrypt_file(working_copy_path, encrypted_path, passphrase)


def _secure_delete(path: Path) -> None:
    """Best-effort overwrite-then-delete. Not a guarantee on SSDs/journaling filesystems."""
    try:
        length = path.stat().st_size
        with open(path, "r+b") as handle:
            handle.write(b"\x00" * length)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError:
        pass
    path.unlink(missing_ok=True)


def close_encrypted_database(encrypted_path: Path, working_copy_path: Path, passphrase: str) -> None:
    """Re-encrypt the working copy and remove the plaintext copy.

    If encryption fails, the working copy is left in place (so no data is
    lost) and the exception propagates to the caller.
    """
    encrypt_snapshot(encrypted_path, working_copy_path, passphrase)
    _secure_delete(working_copy_path)


def finalize_active_session() -> None:
    """Re-encrypt and clean up the active session's working copy, if any."""
    session = _active_session
    if session is None:
        return
    close_encrypted_database(session.encrypted_path, session.working_copy_path, session.passphrase)
    set_active_session(None)
