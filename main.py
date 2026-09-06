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

from db import init_db
from ui.main_window import MainWindow


def main():
    init_db()

    app = ttk.Window(title="Bastion Command", themename="darkly", size=(1000, 700))
    MainWindow(app)
    app.mainloop()


if __name__ == "__main__":
    main()
