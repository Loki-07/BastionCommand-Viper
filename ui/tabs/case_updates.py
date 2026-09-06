"""Case Update Log — a dated narrative update history shown at the bottom of the
Overview tab. Distinct from the Timeline (discrete incident events), RCA/AAR
(post-analysis), and the CTI Running Assessment (intel-focused) — this is a simple
running log of case-status updates ("as of <date>, here's where things stand").
"""

import tkinter as tk
from datetime import date

import ttkbootstrap as ttk

from db.models import CaseUpdate
from ui.tabs.list_form_tab import ListFormTab
from ui.widgets import date_entry

_PREVIEW_LENGTH = 80


class CaseUpdatesTab(ListFormTab):
    columns = ("date", "summary")
    column_headings = {"date": "Date", "summary": "Summary"}
    model = CaseUpdate

    def build_form(self, parent) -> None:
        parent.columnconfigure(1, weight=1)

        ttk.Label(parent, text="Date*").grid(row=0, column=0, sticky="w")
        self.date_var = tk.StringVar()
        date_entry(parent, self.date_var, width=12).grid(row=0, column=1, sticky="w")

        ttk.Label(parent, text="Summary*").grid(row=1, column=0, sticky="nw", pady=(6, 0))
        self.summary_text = ttk.Text(parent, width=60, height=3)
        self.summary_text.grid(row=1, column=1, sticky="ew", pady=(6, 0))

        self.reset_form()

    def row_values(self, record: CaseUpdate) -> tuple:
        preview = record.summary if len(record.summary) <= _PREVIEW_LENGTH else (
            record.summary[:_PREVIEW_LENGTH].rstrip() + "…"
        )
        return (record.date, preview)

    def query_all(self, session, case_id: int):
        return (
            session.query(CaseUpdate)
            .filter_by(case_id=case_id)
            .order_by(CaseUpdate.date.desc(), CaseUpdate.created_at.desc())
            .all()
        )

    def load_form(self, record: CaseUpdate) -> None:
        self.date_var.set(record.date)
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert("1.0", record.summary)

    def read_form(self) -> dict:
        date = self.date_var.get().strip()
        if not date:
            raise ValueError("Date is required.")
        summary = self.summary_text.get("1.0", tk.END).strip()
        if not summary:
            raise ValueError("Summary is required.")
        return {"date": date, "summary": summary}

    def reset_form(self) -> None:
        self.date_var.set(date.today().strftime("%Y-%m-%d"))
        self.summary_text.delete("1.0", tk.END)
