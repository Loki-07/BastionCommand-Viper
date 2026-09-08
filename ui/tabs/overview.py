"""Overview tab — view/edit the case's own fields (name, status, description, etc.)."""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk

from db import Case, get_session
from ui.constants import STATUS_OPTIONS
from ui.tabs.case_updates import CaseUpdatesTab


class OverviewTab(ttk.Frame):
    def __init__(self, master, case_id: int):
        super().__init__(master, padding=15)
        self.case_id = case_id

        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Case Name*").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.case_name_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.case_name_var).grid(
            row=0, column=1, columnspan=3, sticky="ew", pady=(0, 6)
        )

        ttk.Label(self, text="Status").grid(row=1, column=0, sticky="w", pady=(0, 6))
        self.status_var = tk.StringVar()
        ttk.Combobox(
            self, textvariable=self.status_var, values=STATUS_OPTIONS, state="readonly", width=20
        ).grid(row=1, column=1, sticky="w", pady=(0, 6))

        ttk.Label(self, text="Priority Level (P) (1-5)").grid(row=1, column=2, sticky="w", pady=(0, 6))
        self.impact_var = tk.IntVar(value=1)
        ttk.Spinbox(self, from_=1, to=5, textvariable=self.impact_var, width=5).grid(
            row=1, column=3, sticky="w", pady=(0, 6)
        )

        ttk.Label(self, text="Incident Number").grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.incident_number_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.incident_number_var).grid(
            row=2, column=1, sticky="ew", pady=(0, 6)
        )

        ttk.Label(self, text="Urgency (1-5)").grid(row=2, column=2, sticky="w", pady=(0, 6))
        self.urgency_var = tk.IntVar(value=1)
        ttk.Spinbox(self, from_=1, to=5, textvariable=self.urgency_var, width=5).grid(
            row=2, column=3, sticky="w", pady=(0, 6)
        )

        ttk.Label(self, text="Incident Manager").grid(row=3, column=0, sticky="w", pady=(0, 6))
        self.incident_manager_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.incident_manager_var).grid(
            row=3, column=1, columnspan=3, sticky="ew", pady=(0, 6)
        )

        ttk.Label(self, text="Summary").grid(row=4, column=0, sticky="nw", pady=(0, 6))
        self.summary_text = ttk.Text(self, width=60, height=3)
        self.summary_text.grid(row=4, column=1, columnspan=3, sticky="ew", pady=(0, 6))

        ttk.Label(self, text="Description").grid(row=5, column=0, sticky="nw", pady=(0, 6))
        self.description_text = ttk.Text(self, width=60, height=6)
        self.description_text.grid(row=5, column=1, columnspan=3, sticky="ew", pady=(0, 6))

        self.created_at_label = ttk.Label(self, text="", bootstyle="secondary")
        self.created_at_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=(6, 0))

        ttk.Button(self, text="Save", bootstyle="success", command=self._save).grid(
            row=6, column=3, sticky="e", pady=(6, 0)
        )

        ttk.Separator(self).grid(row=7, column=0, columnspan=4, sticky="ew", pady=(12, 6))

        ttk.Label(self, text="Case Updates", font="-weight bold").grid(
            row=8, column=0, columnspan=4, sticky="w"
        )
        self.rowconfigure(9, weight=1)
        updates_frame = CaseUpdatesTab(self, case_id)
        updates_frame.tree.configure(height=4)
        updates_frame.grid(row=9, column=0, columnspan=4, sticky="nsew")

        self._load()

    def _load(self) -> None:
        with get_session() as session:
            case = session.get(Case, self.case_id)
            if case is None:
                return
            self.case_name_var.set(case.case_name)
            self.status_var.set(case.status)
            self.impact_var.set(case.impact)
            self.urgency_var.set(case.urgency)
            self.incident_number_var.set(case.incident_number or "")
            self.incident_manager_var.set(case.incident_manager or "")
            self.summary_text.delete("1.0", tk.END)
            self.summary_text.insert("1.0", case.summary or "")
            self.description_text.delete("1.0", tk.END)
            self.description_text.insert("1.0", case.description or "")
            self.created_at_label.configure(text=f"Created: {case.created_at.strftime('%Y-%m-%d %H:%M')}")

    def _save(self) -> None:
        case_name = self.case_name_var.get().strip()
        if not case_name:
            messagebox.showerror("Invalid input", "Case name is required.")
            return

        try:
            with get_session() as session:
                case = session.get(Case, self.case_id)
                if case is None:
                    messagebox.showerror("Not found", "This case no longer exists.")
                    return
                case.case_name = case_name
                case.status = self.status_var.get()
                case.impact = self.impact_var.get()
                case.urgency = self.urgency_var.get()
                case.incident_number = self.incident_number_var.get().strip() or None
                case.incident_manager = self.incident_manager_var.get().strip() or None
                case.summary = self.summary_text.get("1.0", tk.END).strip()
                case.description = self.description_text.get("1.0", tk.END).strip()
        except Exception as exc:  # noqa: BLE001 - surface unexpected DB errors to the user
            messagebox.showerror("Save failed", f"Could not save this case:\n{exc}")
            return

        messagebox.showinfo("Saved", "Case updated.")

