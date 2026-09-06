"""New Case modal dialog."""

import tkinter as tk
from typing import Callable

import ttkbootstrap as ttk

from db import Case, get_session


class NewCaseDialog(ttk.Toplevel):
    """Minimal form to create a new Case: case_name, description, impact, urgency."""

    def __init__(self, master, on_created: Callable[[], None]):
        super().__init__(title="New Case", master=master, transient=master, resizable=(False, False))
        self.on_created = on_created

        form = ttk.Frame(self, padding=15)
        form.pack(fill="both", expand=True)
        form.columnconfigure(0, weight=1)

        ttk.Label(form, text="Case Name*").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.case_name_var = tk.StringVar()
        name_entry = ttk.Entry(form, textvariable=self.case_name_var, width=40)
        name_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        name_entry.bind("<Return>", lambda _event: self._save())
        name_entry.focus_set()

        ttk.Label(form, text="Description").grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.description_text = ttk.Text(form, width=40, height=5)
        self.description_text.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ttk.Label(form, text="Impact (1-5)").grid(row=4, column=0, sticky="w")
        self.impact_var = tk.IntVar(value=1)
        ttk.Spinbox(form, from_=1, to=5, textvariable=self.impact_var, width=5).grid(row=4, column=1, sticky="w")

        ttk.Label(form, text="Urgency (1-5)").grid(row=5, column=0, sticky="w", pady=(6, 10))
        self.urgency_var = tk.IntVar(value=1)
        ttk.Spinbox(form, from_=1, to=5, textvariable=self.urgency_var, width=5).grid(
            row=5, column=1, sticky="w", pady=(6, 10)
        )

        self.error_label = ttk.Label(form, text="", bootstyle="danger")
        self.error_label.grid(row=6, column=0, columnspan=2, sticky="w")

        button_row = ttk.Frame(form)
        button_row.grid(row=7, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(button_row, text="Cancel", bootstyle="secondary", command=self.destroy).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(button_row, text="Save", bootstyle="success", command=self._save).pack(side="left")

        self.bind("<Escape>", lambda _event: self.destroy())

    def _save(self):
        case_name = self.case_name_var.get().strip()
        if not case_name:
            self.error_label.configure(text="Case name is required.")
            return

        description = self.description_text.get("1.0", tk.END).strip() or None

        try:
            with get_session() as session:
                session.add(
                    Case(
                        case_name=case_name,
                        description=description,
                        impact=self.impact_var.get(),
                        urgency=self.urgency_var.get(),
                    )
                )
        except Exception as exc:  # noqa: BLE001 - surface unexpected DB errors to the user
            self.error_label.configure(text=f"Could not save: {exc}")
            return

        self.on_created()
        self.destroy()
