"""Dialogs for setting or entering a Viper database encryption passphrase."""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk


class _PassphraseDialog(ttk.Toplevel):
    def __init__(self, master, *, title: str, confirm: bool, prompt: str):
        super().__init__(title=title, master=master, transient=master)
        self.result: str | None = None
        self.confirm = confirm

        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda _event: self._cancel())

        content = ttk.Frame(self, padding=16)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)

        ttk.Label(content, text=prompt, wraplength=360, justify="left").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )

        ttk.Label(content, text="Passphrase").grid(row=1, column=0, sticky="w", pady=(12, 0))
        self.passphrase_var = tk.StringVar()
        entry = ttk.Entry(content, textvariable=self.passphrase_var, show="*", width=40)
        entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        entry.bind("<Return>", lambda _event: self._accept())
        entry.focus_set()

        next_row = 3
        if confirm:
            ttk.Label(content, text="Confirm passphrase").grid(row=3, column=0, sticky="w", pady=(10, 0))
            self.confirm_var = tk.StringVar()
            confirm_entry = ttk.Entry(content, textvariable=self.confirm_var, show="*", width=40)
            confirm_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 0))
            confirm_entry.bind("<Return>", lambda _event: self._accept())
            next_row = 5

        ttk.Button(content, text="Cancel", command=self._cancel).grid(
            row=next_row, column=0, sticky="w", pady=(14, 0)
        )
        ttk.Button(content, text="OK", bootstyle="success", command=self._accept).grid(
            row=next_row, column=1, sticky="e", pady=(14, 0)
        )

        self.grab_set()
        self.focus_set()

    def _accept(self) -> None:
        passphrase = self.passphrase_var.get()
        if not passphrase:
            messagebox.showerror("Passphrase required", "Enter a passphrase to continue.", parent=self)
            return
        if self.confirm:
            if len(passphrase) < 8:
                messagebox.showerror(
                    "Passphrase too short", "Use a passphrase of at least 8 characters.", parent=self
                )
                return
            if passphrase != self.confirm_var.get():
                messagebox.showerror(
                    "Passphrases do not match", "Re-enter matching passphrases.", parent=self
                )
                return
        self.result = passphrase
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()


def prompt_new_passphrase(master) -> str | None:
    """Ask the user to set (and confirm) a passphrase for a new encrypted database."""
    dialog = _PassphraseDialog(
        master,
        title="Set Database Passphrase",
        confirm=True,
        prompt=(
            "Set a passphrase to encrypt this database at rest.\n\n"
            "Viper does not store this passphrase anywhere. If it is lost, "
            "the database cannot be recovered."
        ),
    )
    master.wait_window(dialog)
    return dialog.result


def prompt_unlock_passphrase(master, *, retry: bool = False) -> str | None:
    """Ask the user for the passphrase to unlock an existing encrypted database."""
    prompt = "Enter the passphrase for this encrypted database."
    if retry:
        prompt = "Incorrect passphrase — please try again.\n\n" + prompt
    dialog = _PassphraseDialog(master, title="Unlock Database", confirm=False, prompt=prompt)
    master.wait_window(dialog)
    return dialog.result
