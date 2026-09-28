"""
Bastion Command (Viper) - Desktop Entry Point
==============================================

Pure-Python desktop rewrite of Bastion Command (CSIM). Single-process
Tkinter/ttkbootstrap application backed by a local SQLite database via
SQLAlchemy. No server, no browser, no Node/React runtime required.

Run with:
    python main.py
"""

import ttkbootstrap as ttk
from tkinter import messagebox

from db import init_db
from ui.database_locations import remember_database
from ui.database_selection_dialog import select_database_path
from ui.main_window import MainWindow
from ui.theme import apply_bastion_theme
from ui.widgets import get_app_icon


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

        try:
            init_db(selection.path)
            remember_database(selection.path, selection.save_as_favorite)
            break
        except Exception as exc:  # noqa: BLE001 - show an actionable startup error
            messagebox.showerror("Database could not be opened", f"Viper could not open this database:\n{exc}")

    MainWindow(app)
    app.mainloop()


if __name__ == "__main__":
    main()
