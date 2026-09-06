"""Timeline tab — chronological TimelineEvent records for a case."""

import tkinter as tk
from datetime import datetime

import ttkbootstrap as ttk

from db import get_session
from db.models import TimelineEvent
from ui.constants import EVENT_TYPES, TIMELINE_TYPE_COLORS
from ui.tabs.list_form_tab import ListFormTab


class TimelineTab(ListFormTab):
    columns = ("timestamp", "type", "description")
    column_headings = {"timestamp": "Timestamp", "type": "Type", "description": "Description"}
    model = TimelineEvent

    def __init__(self, master, case_id: int):
        super().__init__(master, case_id)
        for event_type, color in TIMELINE_TYPE_COLORS.items():
            self.tree.tag_configure(f"type_{event_type}", foreground=color)

    def build_form(self, parent) -> None:
        parent.columnconfigure(1, weight=1)

        ttk.Label(parent, text="Timestamp (YYYY-MM-DD HH:MM)").grid(row=0, column=0, sticky="w")
        self.timestamp_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.timestamp_var, width=25).grid(row=0, column=1, sticky="w")

        ttk.Label(parent, text="Type").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.type_var = tk.StringVar(value=EVENT_TYPES[0])
        ttk.Combobox(
            parent, textvariable=self.type_var, values=EVENT_TYPES, state="readonly", width=18
        ).grid(row=0, column=3, sticky="w")

        ttk.Label(parent, text="Description*").grid(row=1, column=0, sticky="nw", pady=(6, 0))
        self.description_text = ttk.Text(parent, width=60, height=3)
        self.description_text.grid(row=1, column=1, columnspan=3, sticky="ew", pady=(6, 0))

        self.reset_form()

    def row_values(self, record: TimelineEvent) -> tuple:
        return (record.timestamp.strftime("%Y-%m-%d %H:%M"), record.type, record.description)

    def query_all(self, session, case_id: int):
        return (
            session.query(TimelineEvent)
            .filter_by(case_id=case_id)
            .order_by(TimelineEvent.timestamp)
            .all()
        )

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        with get_session() as session:
            for record in self.query_all(session, self.case_id):
                tag = f"type_{record.type}" if record.type in TIMELINE_TYPE_COLORS else ""
                self.tree.insert(
                    "", "end", iid=str(record.id), values=self.row_values(record), tags=(tag,)
                )

    def load_form(self, record: TimelineEvent) -> None:
        self.timestamp_var.set(record.timestamp.strftime("%Y-%m-%d %H:%M"))
        self.type_var.set(record.type)
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", record.description)

    def read_form(self) -> dict:
        description = self.description_text.get("1.0", tk.END).strip()
        if not description:
            raise ValueError("Description is required.")
        try:
            timestamp = datetime.strptime(self.timestamp_var.get().strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError("Timestamp must be in the format YYYY-MM-DD HH:MM.")
        return {"timestamp": timestamp, "type": self.type_var.get(), "description": description}

    def reset_form(self) -> None:
        self.timestamp_var.set(datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
        self.type_var.set(EVENT_TYPES[0])
        self.description_text.delete("1.0", tk.END)
