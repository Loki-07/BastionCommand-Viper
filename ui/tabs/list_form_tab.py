"""
Shared list+form pattern used by the Timeline, Affected Systems, Affected Users,
and IOCs tabs: a Treeview of case-scoped child records on top, an inline add/edit
form below, and Save/Delete/Clear actions.

Subclasses provide the model-specific pieces (columns, form widgets, mapping
between form values and model fields); this base handles the generic wiring:
loading rows, selection -> form, save (insert or update), delete, and refresh.
"""

from tkinter import messagebox
from typing import Any

import ttkbootstrap as ttk

from db import get_session


class ListFormTab(ttk.Frame):
    #: Treeview column ids, in display order.
    columns: tuple[str, ...] = ()
    #: Treeview column -> heading text.
    column_headings: dict[str, str] = {}
    #: SQLAlchemy model class for this tab's records.
    model: type = None  # type: ignore[assignment]

    def __init__(self, master, case_id: int):
        super().__init__(master, padding=10)
        self.case_id = case_id
        self._editing_id: int | None = None

        tree_frame = ttk.Frame(self)
        form_container = ttk.Labelframe(self, text="Add / Edit", padding=10)
        button_row = ttk.Frame(self)

        # Pack fixed-height widgets from the bottom first so the tree gets the
        # remaining space.
        button_row.pack(side="bottom", fill="x", pady=(8, 0))
        form_container.pack(side="bottom", fill="x")
        tree_frame.pack(side="top", fill="both", expand=True)

        self.tree = ttk.Treeview(
            tree_frame, columns=self.columns, show="headings", selectmode="browse", height=8
        )
        for col in self.columns:
            self.tree.heading(col, text=self.column_headings.get(col, col.title()))
            self.tree.column(col, width=140, anchor="w")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Delete>", lambda _event: self._on_delete())

        self.build_form(form_container)

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

        self.refresh()

    # --- Hooks for subclasses -------------------------------------------------

    def build_form(self, parent: ttk.Labelframe) -> None:
        """Build form widgets into `parent` and store their tk variables on self."""
        raise NotImplementedError

    def row_values(self, record: Any) -> tuple:
        """Return the Treeview row values (matching `self.columns`) for a record."""
        raise NotImplementedError

    def load_form(self, record: Any) -> None:
        """Populate the form fields from an existing record, for editing."""
        raise NotImplementedError

    def read_form(self) -> dict:
        """Read form fields into a dict of model field names -> values.

        Raise ValueError with a user-facing message if validation fails.
        """
        raise NotImplementedError

    def reset_form(self) -> None:
        """Clear the form back to its default/empty state."""
        raise NotImplementedError

    def query_all(self, session, case_id: int) -> list:
        """Return all records for this case, in display order."""
        return (
            session.query(self.model)
            .filter_by(case_id=case_id)
            .order_by(self.model.id)
            .all()
        )

    def new_instance(self, case_id: int, data: dict) -> Any:
        """Build a new model instance from form data (for Add New)."""
        return self.model(case_id=case_id, **data)

    def apply_updates(self, record: Any, data: dict) -> None:
        """Apply form data onto an existing record (for Save Changes)."""
        for key, value in data.items():
            setattr(record, key, value)

    # --- Generic wiring ---------------------------------------------------

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        with get_session() as session:
            for record in self.query_all(session, self.case_id):
                self.tree.insert("", "end", iid=str(record.id), values=self.row_values(record))

    def _on_select(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        record_id = int(selection[0])
        with get_session() as session:
            record = session.get(self.model, record_id)
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
                    record = session.get(self.model, self._editing_id)
                    if record is None:
                        messagebox.showerror("Not found", "That record no longer exists.")
                    else:
                        self.apply_updates(record, data)
                else:
                    session.add(self.new_instance(self.case_id, data))
        except Exception as exc:  # noqa: BLE001 - surface unexpected DB errors to the user
            messagebox.showerror("Save failed", f"Could not save this record:\n{exc}")
            return

        self.refresh()
        self._on_clear()

    def _on_delete(self) -> None:
        if self._editing_id is None:
            messagebox.showinfo("No selection", "Select a row first.")
            return
        if not messagebox.askyesno("Delete", "Delete this record? This cannot be undone."):
            return

        try:
            with get_session() as session:
                record = session.get(self.model, self._editing_id)
                if record is not None:
                    session.delete(record)
        except Exception as exc:  # noqa: BLE001 - surface unexpected DB errors to the user
            messagebox.showerror("Delete failed", f"Could not delete this record:\n{exc}")
            return

        self.refresh()
        self._on_clear()

    def _on_clear(self) -> None:
        self._editing_id = None
        self.tree.selection_remove(*self.tree.selection())
        self.reset_form()
