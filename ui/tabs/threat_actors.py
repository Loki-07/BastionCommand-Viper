"""Threat Actors panel — embedded in the CTI > Running Assessment tab. Tracks who is
believed to be behind the activity for a case: name, type, and affiliation.

Lets the user either add a brand-new threat actor or reuse one already recorded
against another case in the database. When an actor is selected from the database (or
an existing row in this case's own list is selected), a side panel lists every other
case that same actor is also linked to.
"""

import tkinter as tk
from typing import Callable

import ttkbootstrap as ttk

from db import get_session
from db.models import Case, ThreatActor
from ui.constants import THREAT_ACTOR_TYPES
from ui.tabs.list_form_tab import ListFormTab

NEW_ACTOR_LABEL = "(new threat actor)"


class _CaseThreatActorList(ListFormTab):
    """The per-case add/edit list of threat actors — the usual list+form pattern,
    extended to report the currently-focused actor name upward so the sibling
    "Other Cases" panel can stay in sync.
    """

    columns = ("name", "actor_type", "affiliation")
    column_headings = {
        "name": "Threat Actor Name",
        "actor_type": "Type",
        "affiliation": "Affiliation",
    }
    model = ThreatActor

    def __init__(
        self,
        master,
        case_id: int,
        on_focus_change: Callable[[str | None], None],
        on_data_changed: Callable[[], None],
    ):
        self._on_focus_change = on_focus_change
        self._on_data_changed = on_data_changed
        super().__init__(master, case_id)

    def build_form(self, parent) -> None:
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(3, weight=1)

        ttk.Label(parent, text="Threat Actor Name*").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.name_var).grid(
            row=0, column=1, columnspan=3, sticky="ew"
        )

        ttk.Label(parent, text="Type").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.actor_type_var = tk.StringVar(value=THREAT_ACTOR_TYPES[0])
        ttk.Combobox(
            parent,
            textvariable=self.actor_type_var,
            values=THREAT_ACTOR_TYPES,
            state="readonly",
            width=18,
        ).grid(row=1, column=1, sticky="w", pady=(6, 0))

        ttk.Label(parent, text="Affiliation").grid(row=1, column=2, sticky="w", padx=(12, 0), pady=(6, 0))
        self.affiliation_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.affiliation_var).grid(
            row=1, column=3, sticky="ew", pady=(6, 0)
        )

    def row_values(self, record: ThreatActor) -> tuple:
        return (record.name, record.actor_type, record.affiliation or "")

    def load_form(self, record: ThreatActor) -> None:
        self.name_var.set(record.name)
        self.actor_type_var.set(record.actor_type)
        self.affiliation_var.set(record.affiliation or "")

    def read_form(self) -> dict:
        name = self.name_var.get().strip()
        if not name:
            raise ValueError("Threat actor name is required.")

        return {
            "name": name,
            "actor_type": self.actor_type_var.get(),
            "affiliation": self.affiliation_var.get().strip() or None,
        }

    def reset_form(self) -> None:
        self.name_var.set("")
        self.actor_type_var.set(THREAT_ACTOR_TYPES[0])
        self.affiliation_var.set("")

    def apply_existing(self, name: str, actor_type: str, affiliation: str | None) -> None:
        """Pre-fill the form from an existing database-wide threat actor record, as a
        brand-new (not-yet-saved) association to this case."""
        self._on_clear()
        self.name_var.set(name)
        self.actor_type_var.set(actor_type)
        self.affiliation_var.set(affiliation or "")
        self._on_focus_change(name)

    def _on_select(self, _event=None) -> None:
        super()._on_select(_event)
        if self._editing_id is not None:
            self._on_focus_change(self.name_var.get().strip() or None)

    def _on_clear(self) -> None:
        super()._on_clear()
        self._on_focus_change(None)

    def refresh(self) -> None:
        super().refresh()
        self._on_data_changed()


class ThreatActorsTab(ttk.Frame):
    """Composite panel: an add/edit list of this case's threat actors on the left, plus
    a right-hand "Other Cases" panel (about half the width) showing every other case
    the currently-focused threat actor is also linked to.
    """

    def __init__(self, master, case_id: int):
        super().__init__(master)
        self.case_id = case_id

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        picker_row = ttk.Frame(self)
        picker_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(picker_row, text="Use existing threat actor from database:").pack(side="left")
        self.existing_var = tk.StringVar(value=NEW_ACTOR_LABEL)
        self.existing_combo = ttk.Combobox(
            picker_row, textvariable=self.existing_var, state="readonly", width=30
        )
        self.existing_combo.pack(side="left", padx=(6, 0))
        self.existing_combo.bind("<<ComboboxSelected>>", self._on_pick_existing)

        self.case_list = _CaseThreatActorList(
            self,
            case_id,
            on_focus_change=self._refresh_associated_cases,
            on_data_changed=self._refresh_existing_options,
        )
        self.case_list.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

        associated_frame = ttk.Labelframe(
            self, text="Other Cases With This Threat Actor", padding=10
        )
        associated_frame.grid(row=0, column=1, rowspan=2, sticky="nsew")
        associated_frame.columnconfigure(0, weight=1)
        associated_frame.rowconfigure(1, weight=1)

        self.associated_hint = ttk.Label(
            associated_frame,
            text="Select or add a threat actor to see other cases it's linked to.",
            bootstyle="secondary",
            wraplength=220,
        )
        self.associated_hint.grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.associated_tree = ttk.Treeview(
            associated_frame, columns=("case_name", "status"), show="headings", selectmode="browse"
        )
        self.associated_tree.heading("case_name", text="Case")
        self.associated_tree.heading("status", text="Status")
        self.associated_tree.column("case_name", width=160, anchor="w")
        self.associated_tree.column("status", width=100, anchor="w")
        self.associated_tree.grid(row=1, column=0, sticky="nsew")

        self._refresh_existing_options()

    def _refresh_existing_options(self) -> None:
        with get_session() as session:
            names = (
                session.query(ThreatActor.name).distinct().order_by(ThreatActor.name).all()
            )
        self.existing_combo.configure(values=[NEW_ACTOR_LABEL, *(n for (n,) in names)])
        if self.existing_var.get() not in self.existing_combo.cget("values"):
            self.existing_var.set(NEW_ACTOR_LABEL)

    def _on_pick_existing(self, _event=None) -> None:
        name = self.existing_var.get()
        if name == NEW_ACTOR_LABEL:
            return
        with get_session() as session:
            record = (
                session.query(ThreatActor)
                .filter_by(name=name)
                .order_by(ThreatActor.created_at.desc())
                .first()
            )
        if record is None:
            return
        self.case_list.apply_existing(record.name, record.actor_type, record.affiliation)

    def _refresh_associated_cases(self, name: str | None) -> None:
        self.associated_tree.delete(*self.associated_tree.get_children())
        if not name:
            self.associated_hint.configure(
                text="Select or add a threat actor to see other cases it's linked to."
            )
            return

        with get_session() as session:
            rows = (
                session.query(Case.case_name, Case.status)
                .join(ThreatActor, ThreatActor.case_id == Case.id)
                .filter(ThreatActor.name == name, ThreatActor.case_id != self.case_id)
                .distinct()
                .order_by(Case.case_name)
                .all()
            )

        for case_name, status in rows:
            self.associated_tree.insert("", "end", values=(case_name, status))

        if rows:
            self.associated_hint.configure(
                text=f'"{name}" is also linked to {len(rows)} other case(s).'
            )
        else:
            self.associated_hint.configure(text=f'No other cases are linked to "{name}" yet.')
