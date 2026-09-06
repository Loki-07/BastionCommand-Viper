"""Main window — case list, toolbar, and case-detail launcher."""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk

from db import Case, get_session
from ui.case_detail_window import CaseDetailWindow
from ui.constants import STATUS_OPTIONS
from ui.expert_finder_window import ExpertFinderWindow
from ui.new_case_dialog import NewCaseDialog
from ui.timezone_converter_window import TimezoneConverterWindow

COLUMNS = ("case_name", "status", "impact", "urgency", "created_at")
COLUMN_HEADINGS = {
    "case_name": "Case Name",
    "status": "Status",
    "impact": "Impact",
    "urgency": "Urgency",
    "created_at": "Created",
}
ALL_STATUSES_LABEL = "All Statuses"


class MainWindow(ttk.Frame):
    """Root frame: case list Treeview + toolbar. One instance lives in the app window."""

    def __init__(self, master):
        super().__init__(master, padding=10)
        self.pack(fill="both", expand=True)

        self._sort_column = "created_at"
        self._sort_reverse = True

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="New Case", bootstyle="success", command=self._open_new_case_dialog).pack(
            side="left"
        )
        ttk.Button(toolbar, text="Open Case", command=self._open_selected_case).pack(side="left", padx=(8, 0))
        ttk.Button(
            toolbar, text="Delete Case", bootstyle="danger-outline", command=self._delete_selected_case
        ).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Expert Finder", command=self._open_expert_finder).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(toolbar, text="Time Zone Converter", command=self._open_timezone_converter).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(toolbar, text="Refresh", command=self.refresh).pack(side="right")

        filter_row = ttk.Frame(self)
        filter_row.pack(fill="x", pady=(0, 10))
        ttk.Label(filter_row, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_args: self.refresh())
        ttk.Entry(filter_row, textvariable=self.search_var, width=30).pack(side="left", padx=(6, 16))
        ttk.Label(filter_row, text="Status:").pack(side="left")
        self.status_filter_var = tk.StringVar(value=ALL_STATUSES_LABEL)
        ttk.Combobox(
            filter_row,
            textvariable=self.status_filter_var,
            values=[ALL_STATUSES_LABEL, *STATUS_OPTIONS],
            state="readonly",
            width=18,
        ).pack(side="left", padx=(6, 0))
        self.status_filter_var.trace_add("write", lambda *_args: self.refresh())

        self.tree = ttk.Treeview(self, columns=COLUMNS, show="headings", selectmode="browse")
        for col in COLUMNS:
            self.tree.heading(col, text=COLUMN_HEADINGS[col], command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=180 if col == "case_name" else 110, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _event: self._open_selected_case())
        self.tree.bind("<Return>", lambda _event: self._open_selected_case())
        self.tree.bind("<Delete>", lambda _event: self._delete_selected_case())

        self.refresh()

    def refresh(self):
        """Reload the case list from the database, preserving the current selection."""
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())

        search_term = self.search_var.get().strip().lower()
        status_filter = self.status_filter_var.get()

        with get_session() as session:
            column = getattr(Case, self._sort_column)
            order = column.desc() if self._sort_reverse else column.asc()
            query = session.query(Case)
            if status_filter != ALL_STATUSES_LABEL:
                query = query.filter(Case.status == status_filter)
            cases = query.order_by(order).all()
            for case in cases:
                if search_term and search_term not in case.case_name.lower():
                    continue
                self.tree.insert(
                    "",
                    tk.END,
                    iid=str(case.id),
                    values=(
                        case.case_name,
                        case.status,
                        case.impact,
                        case.urgency,
                        case.created_at.strftime("%Y-%m-%d %H:%M"),
                    ),
                )

        for iid in selected:
            if self.tree.exists(iid):
                self.tree.selection_set(iid)

    def _sort_by(self, column: str):
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = False
        self.refresh()

    def _selected_case_id(self) -> int | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _open_new_case_dialog(self):
        NewCaseDialog(self, on_created=self.refresh)

    def _open_expert_finder(self):
        ExpertFinderWindow(self)

    def _open_timezone_converter(self):
        TimezoneConverterWindow(self)

    def _open_selected_case(self):
        case_id = self._selected_case_id()
        if case_id is None:
            messagebox.showinfo("No case selected", "Select a case first.")
            return

        with get_session() as session:
            case = session.get(Case, case_id)
            if case is None:
                messagebox.showerror("Not found", "That case no longer exists.")
                self.refresh()
                return
            case_name = case.case_name

        CaseDetailWindow(self, case_id=case_id, case_name=case_name)

    def _delete_selected_case(self):
        case_id = self._selected_case_id()
        if case_id is None:
            messagebox.showinfo("No case selected", "Select a case first.")
            return

        if not messagebox.askyesno("Delete case", "Delete this case and all its data? This cannot be undone."):
            return

        try:
            with get_session() as session:
                case = session.get(Case, case_id)
                if case is not None:
                    session.delete(case)
        except Exception as exc:  # noqa: BLE001 - surface unexpected DB errors to the user
            messagebox.showerror("Delete failed", f"Could not delete this case:\n{exc}")
            return

        self.refresh()
