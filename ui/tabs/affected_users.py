"""Affected Users tab — AffectedUser CRUD for a case."""

import tkinter as tk

import ttkbootstrap as ttk

from db import get_session
from db.models import AffectedUser
from ui.tabs.list_form_tab import ListFormTab


class AffectedUsersTab(ListFormTab):
    columns = ("name", "username", "email", "systems_affected", "restricted")
    column_headings = {
        "name": "Name",
        "username": "Username",
        "email": "Email",
        "systems_affected": "Systems Affected",
        "restricted": "Restricted Comm.",
    }
    model = AffectedUser

    def __init__(self, master, case_id: int):
        super().__init__(master, case_id)
        self.tree.tag_configure("restricted", foreground="#e06c75")

    def build_form(self, parent) -> None:
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(3, weight=1)

        ttk.Label(parent, text="Name*").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.name_var).grid(row=0, column=1, sticky="ew")

        ttk.Label(parent, text="Username").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.username_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.username_var).grid(row=0, column=3, sticky="ew")

        ttk.Label(parent, text="Email").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.email_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.email_var).grid(row=1, column=1, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="Phone").grid(row=1, column=2, sticky="w", padx=(12, 0), pady=(6, 0))
        self.phone_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.phone_var).grid(row=1, column=3, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="Chat Handle").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.chat_handle_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.chat_handle_var).grid(row=2, column=1, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="Systems Affected").grid(row=2, column=2, sticky="w", padx=(12, 0), pady=(6, 0))
        self.systems_affected_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.systems_affected_var).grid(
            row=2, column=3, sticky="ew", pady=(6, 0)
        )

        self.restricted_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            parent,
            text="Restricted communication (do not contact directly)",
            variable=self.restricted_var,
            bootstyle="danger-round-toggle",
        ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))

        ttk.Label(parent, text="Notes").grid(row=4, column=0, sticky="nw", pady=(6, 0))
        self.notes_text = ttk.Text(parent, width=60, height=3)
        self.notes_text.grid(row=4, column=1, columnspan=3, sticky="ew", pady=(6, 0))

    def row_values(self, record: AffectedUser) -> tuple:
        return (
            record.name,
            record.username or "",
            record.email or "",
            record.systems_affected or "",
            "Yes" if record.restricted_comm else "No",
        )

    def load_form(self, record: AffectedUser) -> None:
        self.name_var.set(record.name)
        self.username_var.set(record.username or "")
        self.email_var.set(record.email or "")
        self.phone_var.set(record.phone or "")
        self.chat_handle_var.set(record.chat_handle or "")
        self.systems_affected_var.set(record.systems_affected or "")
        self.restricted_var.set(record.restricted_comm)
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", record.notes or "")

    def read_form(self) -> dict:
        name = self.name_var.get().strip()
        if not name:
            raise ValueError("Name is required.")
        return {
            "name": name,
            "username": self.username_var.get().strip() or None,
            "email": self.email_var.get().strip() or None,
            "phone": self.phone_var.get().strip() or None,
            "chat_handle": self.chat_handle_var.get().strip() or None,
            "systems_affected": self.systems_affected_var.get().strip() or None,
            "restricted_comm": self.restricted_var.get(),
            "notes": self.notes_text.get("1.0", tk.END).strip() or None,
        }

    def reset_form(self) -> None:
        self.name_var.set("")
        self.username_var.set("")
        self.email_var.set("")
        self.phone_var.set("")
        self.chat_handle_var.set("")
        self.systems_affected_var.set("")
        self.restricted_var.set(False)
        self.notes_text.delete("1.0", tk.END)

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        with get_session() as session:
            for record in self.query_all(session, self.case_id):
                tags = ("restricted",) if record.restricted_comm else ()
                self.tree.insert(
                    "", "end", iid=str(record.id), values=self.row_values(record), tags=tags
                )
