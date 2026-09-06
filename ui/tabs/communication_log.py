"""Communication Log tab — a quick-reference timeline of *when* communications
happened and *what type* they were (not the communication content itself).

Deliberately trimmed from the legacy `CommunicationLog` model (which stored the
actual message template/recipients/body) per the user's simplified scope: just
Date, Type, an optional one-line Summary, and optional longer Notes — opened per-row
for quick reference rather than browsed as full message content.
"""

import tkinter as tk
from datetime import datetime

import ttkbootstrap as ttk

from db.models import CommunicationLogEntry
from ui.constants import COMMUNICATION_TYPES
from ui.tabs.list_form_tab import ListFormTab


class CommunicationLogTab(ListFormTab):
    columns = ("timestamp", "comm_type", "summary")
    column_headings = {
        "timestamp": "Date/Time",
        "comm_type": "Type",
        "summary": "Summary",
    }
    model = CommunicationLogEntry

    def build_form(self, parent) -> None:
        parent.columnconfigure(1, weight=1)

        ttk.Label(parent, text="Timestamp (YYYY-MM-DD HH:MM)").grid(row=0, column=0, sticky="w")
        self.timestamp_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.timestamp_var, width=25).grid(
            row=0, column=1, sticky="w"
        )

        ttk.Label(parent, text="Type").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.comm_type_var = tk.StringVar(value=COMMUNICATION_TYPES[0])
        ttk.Combobox(
            parent,
            textvariable=self.comm_type_var,
            values=COMMUNICATION_TYPES,
            state="readonly",
            width=20,
        ).grid(row=0, column=3, sticky="w")

        ttk.Label(parent, text="Summary").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.summary_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.summary_var).grid(
            row=1, column=1, columnspan=3, sticky="ew", pady=(6, 0)
        )

        ttk.Label(parent, text="Notes").grid(row=2, column=0, sticky="nw", pady=(6, 0))
        self.notes_text = ttk.Text(parent, width=60, height=3)
        self.notes_text.grid(row=2, column=1, columnspan=3, sticky="ew", pady=(6, 0))

        self.reset_form()

    def row_values(self, record: CommunicationLogEntry) -> tuple:
        return (
            record.timestamp.strftime("%Y-%m-%d %H:%M"),
            record.comm_type,
            record.summary or "",
        )

    def query_all(self, session, case_id: int):
        return (
            session.query(CommunicationLogEntry)
            .filter_by(case_id=case_id)
            .order_by(CommunicationLogEntry.timestamp)
            .all()
        )

    def load_form(self, record: CommunicationLogEntry) -> None:
        self.timestamp_var.set(record.timestamp.strftime("%Y-%m-%d %H:%M"))
        self.comm_type_var.set(record.comm_type)
        self.summary_var.set(record.summary or "")
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", record.notes or "")

    def read_form(self) -> dict:
        try:
            timestamp = datetime.strptime(self.timestamp_var.get().strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError("Timestamp must be in the format YYYY-MM-DD HH:MM.")
        return {
            "timestamp": timestamp,
            "comm_type": self.comm_type_var.get(),
            "summary": self.summary_var.get().strip() or None,
            "notes": self.notes_text.get("1.0", tk.END).strip() or None,
        }

    def reset_form(self) -> None:
        self.timestamp_var.set(datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
        self.comm_type_var.set(COMMUNICATION_TYPES[0])
        self.summary_var.set("")
        self.notes_text.delete("1.0", tk.END)
