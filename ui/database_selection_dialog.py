"""Startup dialog for selecting the SQLite database Viper will open."""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from dataclasses import dataclass

import ttkbootstrap as ttk

from db.database import DEFAULT_DB_PATH
from ui.database_locations import (
    is_favorite_database,
    remove_favorite_database,
    saved_database_paths,
)


@dataclass(frozen=True)
class DatabaseSelection:
    path: Path
    save_as_favorite: bool


class DatabaseSelectionDialog(ttk.Toplevel):
    """Modal dialog that selects an existing database or a path for a new one."""

    def __init__(self, master):
        super().__init__(title="Select Viper Database", master=master, transient=master)
        self.result: DatabaseSelection | None = None
        self.path_var = tk.StringVar(value=str(DEFAULT_DB_PATH.resolve()))
        self.favorite_var = tk.BooleanVar(value=is_favorite_database(DEFAULT_DB_PATH))

        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda _event: self._cancel())
        self.bind("<Return>", lambda _event: self._use_database())

        content = ttk.Frame(self, padding=16)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)

        ttk.Label(content, text="Open an existing Viper database or select a new database file.").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(content, text="Database file").grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(content, textvariable=self.path_var, width=62).grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=(4, 0)
        )

        ttk.Label(content, text="Saved locations").grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.saved_locations_combo = ttk.Combobox(content, state="readonly", width=59)
        self.saved_locations_combo.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(4, 0))
        self.saved_locations_combo.bind("<<ComboboxSelected>>", self._select_saved_location)
        self._refresh_saved_locations()

        ttk.Checkbutton(content, text="Save this location as a favorite", variable=self.favorite_var).grid(
            row=5, column=0, sticky="w", pady=(10, 0)
        )
        ttk.Button(content, text="Remove Favorite", command=self._remove_favorite).grid(
            row=5, column=1, sticky="w", padx=(8, 0), pady=(10, 0)
        )
        ttk.Button(content, text="Open Existing...", command=self._open_existing).grid(
            row=6, column=0, sticky="w", pady=(10, 0)
        )
        ttk.Button(content, text="Create New...", command=self._create_new).grid(
            row=6, column=1, sticky="w", padx=(8, 0), pady=(10, 0)
        )
        ttk.Button(content, text="Cancel", command=self._cancel).grid(
            row=6, column=2, sticky="e", pady=(10, 0)
        )
        ttk.Button(content, text="Use Database", bootstyle="success", command=self._use_database).grid(
            row=7, column=2, sticky="e", pady=(8, 0)
        )

        self.grab_set()
        self.focus_set()

    def _open_existing(self) -> None:
        selected_path = filedialog.askopenfilename(
            parent=self,
            title="Open Viper Database",
            filetypes=[("SQLite databases", "*.db *.sqlite *.sqlite3"), ("All files", "*.*")],
        )
        if selected_path:
            self.path_var.set(selected_path)
            self.favorite_var.set(is_favorite_database(Path(selected_path)))

    def _create_new(self) -> None:
        selected_path = filedialog.asksaveasfilename(
            parent=self,
            title="Create Viper Database",
            defaultextension=".db",
            filetypes=[("SQLite databases", "*.db *.sqlite *.sqlite3"), ("All files", "*.*")],
        )
        if selected_path:
            self.path_var.set(selected_path)
            self.favorite_var.set(is_favorite_database(Path(selected_path)))

    def _refresh_saved_locations(self) -> None:
        favorites, recent = saved_database_paths()
        favorite_strings = [str(path) for path in favorites]
        favorite_normalized = {str(path.resolve()).lower() for path in favorites}
        recent_strings = [str(path) for path in recent if str(path.resolve()).lower() not in favorite_normalized]
        self.saved_locations_combo.configure(values=[*favorite_strings, *recent_strings])

    def _select_saved_location(self, _event=None) -> None:
        selected_path = self.saved_locations_combo.get()
        if selected_path:
            self.path_var.set(selected_path)
            self.favorite_var.set(is_favorite_database(Path(selected_path)))

    def _remove_favorite(self) -> None:
        path_text = self.path_var.get().strip()
        if not path_text:
            return
        try:
            remove_favorite_database(Path(path_text))
        except OSError as exc:
            messagebox.showerror("Favorite could not be removed", str(exc), parent=self)
            return
        self.favorite_var.set(False)
        self._refresh_saved_locations()

    def _use_database(self) -> None:
        path_text = self.path_var.get().strip()
        if not path_text:
            messagebox.showerror("Database required", "Select a database file to continue.", parent=self)
            return

        database_path = Path(path_text).expanduser()
        if database_path.exists() and database_path.is_dir():
            messagebox.showerror("Invalid database", "Select a database file, not a folder.", parent=self)
            return
        if not database_path.parent.exists():
            messagebox.showerror(
                "Folder not found",
                "The selected database folder does not exist.",
                parent=self,
            )
            return

        self.result = DatabaseSelection(database_path.resolve(), self.favorite_var.get())
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()


def select_database_path(master) -> DatabaseSelection | None:
    """Show the selection dialog and return the chosen database details, if any."""
    dialog = DatabaseSelectionDialog(master)
    master.wait_window(dialog)
    return dialog.result