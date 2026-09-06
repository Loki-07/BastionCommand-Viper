"""Incident POCs tab — case-specific stakeholders/points-of-contact for escalation
and notifications (distinct from the deferred, Phase 6 global Expert Finder
directory)."""

import tkinter as tk

import ttkbootstrap as ttk

from db.models import IncidentPOC
from ui.constants import POC_STATUS_OPTIONS
from ui.tabs.list_form_tab import ListFormTab


class IncidentPOCsTab(ListFormTab):
    columns = ("name", "role", "status", "bu", "email", "cell")
    column_headings = {
        "name": "Name",
        "role": "Role",
        "status": "Status",
        "bu": "Business Unit",
        "email": "Email",
        "cell": "Cell",
    }
    model = IncidentPOC

    def build_form(self, parent) -> None:
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(3, weight=1)

        ttk.Label(parent, text="Name*").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.name_var).grid(row=0, column=1, sticky="ew")

        ttk.Label(parent, text="Role").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.role_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.role_var).grid(row=0, column=3, sticky="ew")

        ttk.Label(parent, text="Status").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.status_var = tk.StringVar(value=POC_STATUS_OPTIONS[0])
        ttk.Combobox(
            parent,
            textvariable=self.status_var,
            values=POC_STATUS_OPTIONS,
            state="readonly",
            width=18,
        ).grid(row=1, column=1, sticky="w", pady=(6, 0))

        ttk.Label(parent, text="Business Unit").grid(row=1, column=2, sticky="w", padx=(12, 0), pady=(6, 0))
        self.bu_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.bu_var).grid(row=1, column=3, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="Email").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.email_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.email_var).grid(row=2, column=1, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="Cell").grid(row=2, column=2, sticky="w", padx=(12, 0), pady=(6, 0))
        self.cell_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.cell_var).grid(row=2, column=3, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="Time Zone").grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.tz_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.tz_var, width=20).grid(row=3, column=1, sticky="w", pady=(6, 0))

        ttk.Label(parent, text="Notes").grid(row=4, column=0, sticky="nw", pady=(6, 0))
        self.notes_text = ttk.Text(parent, width=60, height=3)
        self.notes_text.grid(row=4, column=1, columnspan=3, sticky="ew", pady=(6, 0))

    def row_values(self, record: IncidentPOC) -> tuple:
        return (
            record.name,
            record.role or "",
            record.status or "",
            record.bu or "",
            record.email or "",
            record.cell or "",
        )

    def load_form(self, record: IncidentPOC) -> None:
        self.name_var.set(record.name)
        self.role_var.set(record.role or "")
        self.status_var.set(record.status or POC_STATUS_OPTIONS[0])
        self.bu_var.set(record.bu or "")
        self.email_var.set(record.email or "")
        self.cell_var.set(record.cell or "")
        self.tz_var.set(record.tz or "")
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", record.notes or "")

    def read_form(self) -> dict:
        name = self.name_var.get().strip()
        if not name:
            raise ValueError("Name is required.")
        return {
            "name": name,
            "role": self.role_var.get().strip() or None,
            "status": self.status_var.get(),
            "bu": self.bu_var.get().strip() or None,
            "email": self.email_var.get().strip() or None,
            "cell": self.cell_var.get().strip() or None,
            "tz": self.tz_var.get().strip() or None,
            "notes": self.notes_text.get("1.0", tk.END).strip() or None,
        }

    def reset_form(self) -> None:
        self.name_var.set("")
        self.role_var.set("")
        self.status_var.set(POC_STATUS_OPTIONS[0])
        self.bu_var.set("")
        self.email_var.set("")
        self.cell_var.set("")
        self.tz_var.set("")
        self.notes_text.delete("1.0", tk.END)
