"""Expert Finder — a global, case-independent directory of experts/resources built up
over time from past cases, so a specific expert can be located again later. Opened
from the main window's toolbar (not from a case-detail window).
"""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk

from db import PointOfContact, get_session
from ui.constants import VENDOR_EMPLOYEE_OPTIONS

COLUMNS = (
    "name",
    "role",
    "team",
    "technology_sme",
    "vendor_employee",
    "vendor_company",
    "specialization",
    "email",
    "cell",
    "tz",
)
COLUMN_HEADINGS = {
    "name": "Name",
    "role": "Role",
    "team": "Team(s)",
    "technology_sme": "Technology/SME",
    "vendor_employee": "Type",
    "vendor_company": "Company",
    "specialization": "Specialization",
    "email": "Email",
    "cell": "Cell",
    "tz": "TZ",
}

_SEARCHABLE_FIELDS = (
    "name",
    "role",
    "team",
    "technology_sme",
    "vendor_company",
    "system_owner",
    "specialization",
)


class ExpertFinderWindow(ttk.Toplevel):
    """Global Expert Finder directory — list + form CRUD, independent of any case."""

    def __init__(self, master):
        super().__init__(title="Expert Finder", master=master, transient=master, size=(1050, 700))
        self._editing_id: int | None = None

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        search_row = ttk.Frame(container)
        search_row.pack(fill="x", pady=(0, 8))
        ttk.Label(search_row, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_args: self.refresh())
        ttk.Entry(search_row, textvariable=self.search_var, width=40).pack(side="left", padx=(6, 0))
        ttk.Label(
            search_row, text="(matches name, role, team, technology, company, system, specialization)",
            bootstyle="secondary",
        ).pack(side="left", padx=(8, 0))

        tree_frame = ttk.Frame(container)
        form_container = ttk.Labelframe(container, text="Add / Edit Expert", padding=10)
        button_row = ttk.Frame(container)

        button_row.pack(side="bottom", fill="x", pady=(8, 0))
        form_container.pack(side="bottom", fill="x")
        tree_frame.pack(side="top", fill="both", expand=True)

        self.tree = ttk.Treeview(
            tree_frame, columns=COLUMNS, show="headings", selectmode="browse", height=10
        )
        for col in COLUMNS:
            self.tree.heading(col, text=COLUMN_HEADINGS[col])
            self.tree.column(col, width=110, anchor="w")
        self.tree.column("name", width=140)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Delete>", lambda _event: self._on_delete())

        self._build_form(form_container)

        ttk.Button(button_row, text="Add New", bootstyle="success", command=self._on_save).pack(
            side="left"
        )
        ttk.Button(button_row, text="Save Changes", command=self._on_save).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(
            button_row, text="Delete", bootstyle="danger-outline", command=self._on_delete
        ).pack(side="left", padx=(8, 0))
        ttk.Button(button_row, text="Clear", command=self._on_clear).pack(side="left", padx=(8, 0))

        self.bind("<Escape>", lambda _event: self.destroy())

        self.refresh()

    def _build_form(self, parent: ttk.Labelframe) -> None:
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(3, weight=1)

        ttk.Label(parent, text="Name*").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.name_var).grid(
            row=0, column=1, sticky="ew", pady=(0, 6)
        )
        ttk.Label(parent, text="Role").grid(row=0, column=2, sticky="w", padx=(12, 0), pady=(0, 6))
        self.role_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.role_var).grid(
            row=0, column=3, sticky="ew", pady=(0, 6)
        )

        ttk.Label(parent, text="Team(s), comma-separated").grid(
            row=1, column=0, sticky="w", pady=(0, 6)
        )
        self.team_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.team_var).grid(
            row=1, column=1, sticky="ew", pady=(0, 6)
        )
        ttk.Label(parent, text="Technology/SME, comma-separated").grid(
            row=1, column=2, sticky="w", padx=(12, 0), pady=(0, 6)
        )
        self.technology_sme_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.technology_sme_var).grid(
            row=1, column=3, sticky="ew", pady=(0, 6)
        )

        ttk.Label(parent, text="Type").grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.vendor_employee_var = tk.StringVar()
        ttk.Combobox(
            parent,
            textvariable=self.vendor_employee_var,
            values=VENDOR_EMPLOYEE_OPTIONS,
            state="readonly",
            width=18,
        ).grid(row=2, column=1, sticky="w", pady=(0, 6))
        ttk.Label(parent, text="Vendor Company").grid(
            row=2, column=2, sticky="w", padx=(12, 0), pady=(0, 6)
        )
        self.vendor_company_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.vendor_company_var).grid(
            row=2, column=3, sticky="ew", pady=(0, 6)
        )

        ttk.Label(parent, text="System Owner").grid(row=3, column=0, sticky="w", pady=(0, 6))
        self.system_owner_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.system_owner_var).grid(
            row=3, column=1, sticky="ew", pady=(0, 6)
        )
        ttk.Label(parent, text="Specialization").grid(
            row=3, column=2, sticky="w", padx=(12, 0), pady=(0, 6)
        )
        self.specialization_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.specialization_var).grid(
            row=3, column=3, sticky="ew", pady=(0, 6)
        )

        ttk.Label(parent, text="Email").grid(row=4, column=0, sticky="w", pady=(0, 6))
        self.email_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.email_var).grid(
            row=4, column=1, sticky="ew", pady=(0, 6)
        )
        ttk.Label(parent, text="Phone").grid(row=4, column=2, sticky="w", padx=(12, 0), pady=(0, 6))
        self.phone_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.phone_var).grid(
            row=4, column=3, sticky="ew", pady=(0, 6)
        )

        ttk.Label(parent, text="Cell").grid(row=5, column=0, sticky="w", pady=(0, 6))
        self.cell_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.cell_var).grid(
            row=5, column=1, sticky="ew", pady=(0, 6)
        )
        ttk.Label(parent, text="TZ").grid(row=5, column=2, sticky="w", padx=(12, 0), pady=(0, 6))
        self.tz_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.tz_var).grid(
            row=5, column=3, sticky="ew", pady=(0, 6)
        )

        ttk.Label(parent, text="Notes").grid(row=6, column=0, sticky="nw", pady=(0, 6))
        self.notes_text = tk.Text(parent, width=60, height=3)
        self.notes_text.grid(row=6, column=1, columnspan=3, sticky="ew", pady=(0, 6))

        self.reset_form()

    def row_values(self, record: PointOfContact) -> tuple:
        return (
            record.name,
            record.role or "",
            record.team or "",
            record.technology_sme or "",
            record.vendor_employee or "",
            record.vendor_company or "",
            record.specialization or "",
            record.email or "",
            record.cell or "",
            record.tz or "",
        )

    def load_form(self, record: PointOfContact) -> None:
        self.name_var.set(record.name)
        self.role_var.set(record.role or "")
        self.team_var.set(record.team or "")
        self.technology_sme_var.set(record.technology_sme or "")
        self.vendor_employee_var.set(record.vendor_employee or "")
        self.vendor_company_var.set(record.vendor_company or "")
        self.system_owner_var.set(record.system_owner or "")
        self.specialization_var.set(record.specialization or "")
        self.email_var.set(record.email or "")
        self.phone_var.set(record.phone or "")
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
            "team": self.team_var.get().strip() or None,
            "technology_sme": self.technology_sme_var.get().strip() or None,
            "vendor_employee": self.vendor_employee_var.get().strip() or None,
            "vendor_company": self.vendor_company_var.get().strip() or None,
            "system_owner": self.system_owner_var.get().strip() or None,
            "specialization": self.specialization_var.get().strip() or None,
            "email": self.email_var.get().strip() or None,
            "phone": self.phone_var.get().strip() or None,
            "cell": self.cell_var.get().strip() or None,
            "tz": self.tz_var.get().strip() or None,
            "notes": self.notes_text.get("1.0", tk.END).strip() or None,
        }

    def reset_form(self) -> None:
        self.name_var.set("")
        self.role_var.set("")
        self.team_var.set("")
        self.technology_sme_var.set("")
        self.vendor_employee_var.set("")
        self.vendor_company_var.set("")
        self.system_owner_var.set("")
        self.specialization_var.set("")
        self.email_var.set("")
        self.phone_var.set("")
        self.cell_var.set("")
        self.tz_var.set("")
        self.notes_text.delete("1.0", tk.END)

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        search_term = self.search_var.get().strip().lower()
        with get_session() as session:
            records = session.query(PointOfContact).order_by(PointOfContact.name).all()
            for record in records:
                if search_term:
                    haystack = " ".join(
                        (getattr(record, field) or "") for field in _SEARCHABLE_FIELDS
                    ).lower()
                    if search_term not in haystack:
                        continue
                self.tree.insert("", "end", iid=str(record.id), values=self.row_values(record))

    def _on_select(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        record_id = int(selection[0])
        with get_session() as session:
            record = session.get(PointOfContact, record_id)
            if record is None:
                self.refresh()
                return
            self.load_form(record)
        self._editing_id = record_id

    def _on_save(self) -> None:
        try:
            data = self.read_form()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        try:
            with get_session() as session:
                if self._editing_id is not None:
                    record = session.get(PointOfContact, self._editing_id)
                    if record is None:
                        messagebox.showerror("Not found", "That record no longer exists.")
                    else:
                        for key, value in data.items():
                            setattr(record, key, value)
                else:
                    session.add(PointOfContact(**data))
        except Exception as exc:  # noqa: BLE001 - surface unexpected DB errors to the user
            messagebox.showerror("Save failed", f"Could not save this expert:\n{exc}")
            return

        self.refresh()
        self._on_clear()

    def _on_delete(self) -> None:
        if self._editing_id is None:
            messagebox.showinfo("No selection", "Select a row first.")
            return
        if not messagebox.askyesno("Delete", "Delete this expert? This cannot be undone."):
            return

        try:
            with get_session() as session:
                record = session.get(PointOfContact, self._editing_id)
                if record is not None:
                    session.delete(record)
        except Exception as exc:  # noqa: BLE001 - surface unexpected DB errors to the user
            messagebox.showerror("Delete failed", f"Could not delete this expert:\n{exc}")
            return

        self.refresh()
        self._on_clear()

    def _on_clear(self) -> None:
        self._editing_id = None
        self.tree.selection_remove(*self.tree.selection())
        self.reset_form()
