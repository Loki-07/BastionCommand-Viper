"""IOCs tab — Indicator of Compromise CRUD for a case."""

import tkinter as tk
from datetime import datetime

import ttkbootstrap as ttk

from db import get_session
from db.models import AffectedSystem, IOC
from ui.constants import IOC_TYPES
from ui.tabs.list_form_tab import ListFormTab
from ui.widgets import date_entry

NO_SYSTEM_LABEL = "(none)"


class IOCsTab(ListFormTab):
    columns = ("type", "value", "source", "detection_date")
    column_headings = {
        "type": "Type",
        "value": "Value",
        "source": "Source",
        "detection_date": "Detected",
    }
    model = IOC

    def build_form(self, parent) -> None:
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(3, weight=1)

        ttk.Label(parent, text="Type").grid(row=0, column=0, sticky="w")
        self.type_var = tk.StringVar(value=IOC_TYPES[0])
        ttk.Combobox(
            parent, textvariable=self.type_var, values=IOC_TYPES, state="readonly", width=18
        ).grid(row=0, column=1, sticky="w")

        ttk.Label(parent, text="Value*").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.value_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.value_var).grid(row=0, column=3, sticky="ew")

        ttk.Label(parent, text="Source").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.source_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.source_var).grid(row=1, column=1, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="Detection Date").grid(
            row=1, column=2, sticky="w", padx=(12, 0), pady=(6, 0)
        )
        self.detection_date_var = tk.StringVar()
        date_entry(parent, self.detection_date_var, width=12).grid(
            row=1, column=3, sticky="w", pady=(6, 0)
        )

        ttk.Label(parent, text="Affected System").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.affected_system_var = tk.StringVar(value=NO_SYSTEM_LABEL)
        self.affected_system_combo = ttk.Combobox(
            parent, textvariable=self.affected_system_var, state="readonly", width=30
        )
        self.affected_system_combo.grid(row=2, column=1, columnspan=3, sticky="w", pady=(6, 0))

        ttk.Label(parent, text="Description").grid(row=3, column=0, sticky="nw", pady=(6, 0))
        self.description_text = ttk.Text(parent, width=60, height=2)
        self.description_text.grid(row=3, column=1, columnspan=3, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="Notes").grid(row=4, column=0, sticky="nw", pady=(6, 0))
        self.notes_text = ttk.Text(parent, width=60, height=2)
        self.notes_text.grid(row=4, column=1, columnspan=3, sticky="ew", pady=(6, 0))

        self._system_id_by_label: dict[str, int] = {}

    def refresh(self) -> None:
        with get_session() as session:
            systems = (
                session.query(AffectedSystem)
                .filter_by(case_id=self.case_id)
                .order_by(AffectedSystem.hostname)
                .all()
            )
            self._system_id_by_label = {s.hostname: s.id for s in systems}
        self.affected_system_combo.configure(values=[NO_SYSTEM_LABEL, *self._system_id_by_label.keys()])

        super().refresh()

    def row_values(self, record: IOC) -> tuple:
        detected = record.detection_date.strftime("%Y-%m-%d") if record.detection_date else ""
        return (record.type, record.value, record.source or "", detected)

    def load_form(self, record: IOC) -> None:
        self.type_var.set(record.type)
        self.value_var.set(record.value)
        self.source_var.set(record.source or "")
        self.detection_date_var.set(
            record.detection_date.strftime("%Y-%m-%d") if record.detection_date else ""
        )
        label = NO_SYSTEM_LABEL
        if record.affected_system_id is not None:
            for hostname, system_id in self._system_id_by_label.items():
                if system_id == record.affected_system_id:
                    label = hostname
                    break
        self.affected_system_var.set(label)
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", record.description or "")
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", record.notes or "")

    def read_form(self) -> dict:
        value = self.value_var.get().strip()
        if not value:
            raise ValueError("Value is required.")

        detection_date = None
        raw_date = self.detection_date_var.get().strip()
        if raw_date:
            try:
                detection_date = datetime.strptime(raw_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Detection date must be in the format YYYY-MM-DD.")

        system_label = self.affected_system_var.get()
        affected_system_id = self._system_id_by_label.get(system_label)

        return {
            "type": self.type_var.get(),
            "value": value,
            "source": self.source_var.get().strip() or None,
            "detection_date": detection_date,
            "affected_system_id": affected_system_id,
            "description": self.description_text.get("1.0", tk.END).strip() or None,
            "notes": self.notes_text.get("1.0", tk.END).strip() or None,
        }

    def reset_form(self) -> None:
        self.type_var.set(IOC_TYPES[0])
        self.value_var.set("")
        self.source_var.set("")
        self.detection_date_var.set("")
        self.affected_system_var.set(NO_SYSTEM_LABEL)
        self.description_text.delete("1.0", tk.END)
        self.notes_text.delete("1.0", tk.END)
