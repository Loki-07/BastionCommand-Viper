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


def main():
    app = ttk.Window(title="Bastion Command", themename="darkly", size=(1000, 700))
    ttk.Label(app, text="Bastion Command (Viper) - scaffold OK", font=("Segoe UI", 14)).pack(pady=40)
    app.mainloop()


if __name__ == "__main__":
    main()
