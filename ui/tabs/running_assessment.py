"""Running Assessment tab — the evolving threat picture during an investigation. One
editable record per case; no version history (unlike RCA/AAR) — just a "Date of
Intelligence" (DOI) freshness timestamp that updates every time it's saved, matching
the legacy model.
"""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk

from db import RunningAssessment, get_session
from ui.tabs.threat_actors import ThreatActorsTab


class RunningAssessmentTab(ttk.Frame):
    def __init__(self, master, case_id: int):
        super().__init__(master, padding=15)
        self.case_id = case_id

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=2)
        self.rowconfigure(5, weight=1)

        ttk.Label(self, text="Running Assessment", font="-weight bold").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )

        self.content_text = ttk.Text(self, width=60, height=10, wrap="word")
        self.content_text.grid(row=1, column=0, sticky="nsew", pady=(0, 6))

        self.status_label = ttk.Label(self, text="", bootstyle="secondary")
        self.status_label.grid(row=2, column=0, sticky="w")

        ttk.Button(self, text="Save", bootstyle="success", command=self._save).grid(
            row=3, column=0, sticky="e", pady=(6, 0)
        )

        ttk.Label(self, text="Threat Actors", font="-weight bold").grid(
            row=4, column=0, sticky="w", pady=(12, 6)
        )
        ThreatActorsTab(self, case_id).grid(row=5, column=0, sticky="nsew")

        self._load()

    def _load(self) -> None:
        with get_session() as session:
            assessment = (
                session.query(RunningAssessment).filter_by(case_id=self.case_id).first()
            )
            self.content_text.delete("1.0", tk.END)
            if assessment is not None:
                self.content_text.insert("1.0", assessment.content or "")
                self.status_label.configure(
                    text=f"Date of Intelligence (DOI): {assessment.doi.strftime('%Y-%m-%d %H:%M')}"
                )
            else:
                self.status_label.configure(
                    text="No running assessment yet for this case — save to create one."
                )

    def _save(self) -> None:
        content = self.content_text.get("1.0", tk.END).strip() or None

        try:
            with get_session() as session:
                assessment = (
                    session.query(RunningAssessment).filter_by(case_id=self.case_id).first()
                )
                if assessment is None:
                    session.add(RunningAssessment(case_id=self.case_id, content=content))
                else:
                    assessment.content = content
        except Exception as exc:  # noqa: BLE001 - surface unexpected DB errors to the user
            messagebox.showerror("Save failed", f"Could not save this assessment:\n{exc}")
            return

        self._load()
        messagebox.showinfo("Saved", "Running assessment updated.")
