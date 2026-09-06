"""Intelligence Report tab — finished intelligence products documenting findings
during an investigation (e.g. "Threat Actor TTPs Analysis")."""

import tkinter as tk

import ttkbootstrap as ttk

from db.models import IntelligenceReport
from ui.tabs.list_form_tab import ListFormTab


class IntelligenceReportTab(ListFormTab):
    columns = ("created_at", "title", "source_url", "has_iocs")
    column_headings = {
        "created_at": "Created",
        "title": "Title",
        "source_url": "Source URL",
        "has_iocs": "Has IOCs",
    }
    model = IntelligenceReport

    def build_form(self, parent) -> None:
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(3, weight=1)

        ttk.Label(parent, text="Title*").grid(row=0, column=0, sticky="w")
        self.title_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.title_var).grid(
            row=0, column=1, columnspan=2, sticky="ew"
        )

        self.has_iocs_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(parent, text="Has IOCs", variable=self.has_iocs_var).grid(
            row=0, column=3, sticky="w"
        )

        ttk.Label(parent, text="Source URL").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.source_url_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.source_url_var).grid(
            row=1, column=1, columnspan=3, sticky="ew", pady=(6, 0)
        )

        ttk.Label(parent, text="BLUF (Bottom Line Up Front)").grid(
            row=2, column=0, sticky="nw", pady=(6, 0)
        )
        self.bluf_text = ttk.Text(parent, width=60, height=2)
        self.bluf_text.grid(row=2, column=1, columnspan=3, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="Description").grid(row=3, column=0, sticky="nw", pady=(6, 0))
        self.description_text = ttk.Text(parent, width=60, height=2)
        self.description_text.grid(row=3, column=1, columnspan=3, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="Data Section (findings/analysis)").grid(
            row=4, column=0, sticky="nw", pady=(6, 0)
        )
        self.data_section_text = ttk.Text(parent, width=60, height=3)
        self.data_section_text.grid(row=4, column=1, columnspan=3, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="IOC List").grid(row=5, column=0, sticky="nw", pady=(6, 0))
        self.ioc_list_text = ttk.Text(parent, width=60, height=2)
        self.ioc_list_text.grid(row=5, column=1, columnspan=3, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="Analyst Comments").grid(row=6, column=0, sticky="nw", pady=(6, 0))
        self.analyst_comments_text = ttk.Text(parent, width=60, height=2)
        self.analyst_comments_text.grid(row=6, column=1, columnspan=3, sticky="ew", pady=(6, 0))

    def row_values(self, record: IntelligenceReport) -> tuple:
        return (
            record.created_at.strftime("%Y-%m-%d %H:%M"),
            record.title,
            record.source_url or "",
            "Yes" if record.has_iocs else "No",
        )

    def load_form(self, record: IntelligenceReport) -> None:
        self.title_var.set(record.title)
        self.has_iocs_var.set(record.has_iocs)
        self.source_url_var.set(record.source_url or "")
        self.bluf_text.delete("1.0", tk.END)
        self.bluf_text.insert("1.0", record.bluf or "")
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", record.description or "")
        self.data_section_text.delete("1.0", tk.END)
        self.data_section_text.insert("1.0", record.data_section or "")
        self.ioc_list_text.delete("1.0", tk.END)
        self.ioc_list_text.insert("1.0", record.ioc_list or "")
        self.analyst_comments_text.delete("1.0", tk.END)
        self.analyst_comments_text.insert("1.0", record.analyst_comments or "")

    def read_form(self) -> dict:
        title = self.title_var.get().strip()
        if not title:
            raise ValueError("Title is required.")
        return {
            "title": title,
            "has_iocs": self.has_iocs_var.get(),
            "source_url": self.source_url_var.get().strip() or None,
            "bluf": self.bluf_text.get("1.0", tk.END).strip() or None,
            "description": self.description_text.get("1.0", tk.END).strip() or None,
            "data_section": self.data_section_text.get("1.0", tk.END).strip() or None,
            "ioc_list": self.ioc_list_text.get("1.0", tk.END).strip() or None,
            "analyst_comments": self.analyst_comments_text.get("1.0", tk.END).strip() or None,
        }

    def reset_form(self) -> None:
        self.title_var.set("")
        self.has_iocs_var.set(False)
        self.source_url_var.set("")
        self.bluf_text.delete("1.0", tk.END)
        self.description_text.delete("1.0", tk.END)
        self.data_section_text.delete("1.0", tk.END)
        self.ioc_list_text.delete("1.0", tk.END)
        self.analyst_comments_text.delete("1.0", tk.END)

    def query_all(self, session, case_id: int):
        return (
            session.query(IntelligenceReport)
            .filter_by(case_id=case_id)
            .order_by(IntelligenceReport.created_at)
            .all()
        )
