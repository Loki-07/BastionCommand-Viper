"""
Bastion Command (Viper) - Desktop Entry Point
==============================================

Pure-Python desktop rewrite of Bastion Command (CSIM). Single-process
Tkinter/ttkbootstrap application backed by a local SQLite database via
SQLAlchemy. No server, no browser, no Node/React runtime required.

Run with:
    python main.py
"""

from pathlib import Path

import ttkbootstrap as ttk
from tkinter import messagebox

from db import close_db, init_db
from security.encrypted_database import (
    EncryptionSession,
    create_encrypted_database,
    encrypt_snapshot,
    finalize_active_session,
    get_active_session,
    open_encrypted_database,
    set_active_session,
)
from security.envelope import InvalidPassphraseError, is_encrypted_container
from ui.database_locations import remember_database
from ui.database_selection_dialog import select_database_path
from ui.main_window import MainWindow
from ui.passphrase_dialog import prompt_new_passphrase, prompt_unlock_passphrase
from ui.theme import apply_bastion_theme
from ui.widgets import get_app_icon


def _resolve_db_path_for_session(app, selection_path: Path) -> Path | None:
    """Work out which plaintext SQLite file `init_db()` should open.

    Handles encryption prompts/decryption as needed and records an
    `EncryptionSession` (via `security.encrypted_database`) when the chosen
    database is encrypted. Returns None if the user cancels.
    """
    if not selection_path.exists():
        set_active_session(None)
        if not messagebox.askyesno(
            "Encrypt Database",
            "Encrypt this new database at rest with a passphrase?",
            parent=app,
        ):
            return selection_path

        passphrase = prompt_new_passphrase(app)
        if passphrase is None:
            return None
        working_copy_path = create_encrypted_database(selection_path)
        set_active_session(EncryptionSession(selection_path, working_copy_path, passphrase))
        return working_copy_path

    if not is_encrypted_container(selection_path):
        set_active_session(None)
        return selection_path

    retry = False
    while True:
        passphrase = prompt_unlock_passphrase(app, retry=retry)
        if passphrase is None:
            return None
        try:
            working_copy_path, _recovered = open_encrypted_database(selection_path, passphrase)
        except InvalidPassphraseError:
            retry = True
            continue
        set_active_session(EncryptionSession(selection_path, working_copy_path, passphrase))
        return working_copy_path


def main():
    app = ttk.Window(title="Bastion Command", themename="darkly", size=(1000, 700))
    apply_bastion_theme(app)
    icon = get_app_icon()
    if icon is not None:
        app.iconphoto(True, icon)

    while True:
        selection = select_database_path(app)
        if selection is None:
            app.destroy()
            return

        engine_db_path = _resolve_db_path_for_session(app, selection.path)
        if engine_db_path is None:
            continue  # user cancelled passphrase entry — back to database selection

        try:
            init_db(engine_db_path)
            session = get_active_session()
            if session is not None and not session.encrypted_path.exists():
                # Brand-new encrypted database — persist the first container now,
                # so a crash before the first clean close still leaves a usable file.
                encrypt_snapshot(session.encrypted_path, session.working_copy_path, session.passphrase)
            remember_database(selection.path, selection.save_as_favorite)
            break
        except Exception as exc:  # noqa: BLE001 - show an actionable startup error
            set_active_session(None)
            messagebox.showerror("Database could not be opened", f"Viper could not open this database:\n{exc}")

    def _on_close():
        try:
            close_db()
            finalize_active_session()
        except Exception as exc:  # noqa: BLE001 - keep the window open so the user can retry
            messagebox.showerror(
                "Could not secure database",
                f"Viper could not re-encrypt the database before closing:\n{exc}\n\n"
                "The window will stay open so you can try again.",
                parent=app,
            )
            return
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", _on_close)

    MainWindow(app)
    app.mainloop()


if __name__ == "__main__":
    main()

