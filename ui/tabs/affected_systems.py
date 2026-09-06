"""Affected Systems tab — AffectedSystem CRUD for a case."""

import tkinter as tk

import ttkbootstrap as ttk

from db.models import AffectedSystem
from ui.constants import ASSET_TYPES
from ui.constants import SYSTEM_STATUS_OPTIONS as STATUS_OPTIONS
from ui.tabs.list_form_tab import ListFormTab


class AffectedSystemsTab(ListFormTab):
    columns = ("hostname", "ip_address", "asset_type", "status")
    column_headings = {
        "hostname": "Hostname",
        "ip_address": "IP Address",
        "asset_type": "Asset Type",
        "status": "Status",
    }
    model = AffectedSystem

    def build_form(self, parent) -> None:
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(3, weight=1)

        ttk.Label(parent, text="Hostname*").grid(row=0, column=0, sticky="w")
        self.hostname_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.hostname_var).grid(row=0, column=1, sticky="ew")

        ttk.Label(parent, text="IP Address").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.ip_address_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.ip_address_var).grid(row=0, column=3, sticky="ew")

        ttk.Label(parent, text="Asset Type").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.asset_type_var = tk.StringVar(value=ASSET_TYPES[1])
        ttk.Combobox(
            parent, textvariable=self.asset_type_var, values=ASSET_TYPES, state="readonly", width=18
        ).grid(row=1, column=1, sticky="w", pady=(6, 0))

        ttk.Label(parent, text="Status").grid(row=1, column=2, sticky="w", padx=(12, 0), pady=(6, 0))
        self.status_var = tk.StringVar(value=STATUS_OPTIONS[0])
        ttk.Combobox(
            parent, textvariable=self.status_var, values=STATUS_OPTIONS, state="readonly", width=18
        ).grid(row=1, column=3, sticky="w", pady=(6, 0))

    def row_values(self, record: AffectedSystem) -> tuple:
        return (record.hostname, record.ip_address or "", record.asset_type, record.status)

    def load_form(self, record: AffectedSystem) -> None:
        self.hostname_var.set(record.hostname)
        self.ip_address_var.set(record.ip_address or "")
        self.asset_type_var.set(record.asset_type)
        self.status_var.set(record.status)

    def read_form(self) -> dict:
        hostname = self.hostname_var.get().strip()
        if not hostname:
            raise ValueError("Hostname is required.")
        return {
            "hostname": hostname,
            "ip_address": self.ip_address_var.get().strip() or None,
            "asset_type": self.asset_type_var.get(),
            "status": self.status_var.get(),
        }

    def reset_form(self) -> None:
        self.hostname_var.set("")
        self.ip_address_var.set("")
        self.asset_type_var.set(ASSET_TYPES[1])
        self.status_var.set(STATUS_OPTIONS[0])
