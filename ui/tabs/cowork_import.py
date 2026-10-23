"""Cowork Import tab — review drafts produced by an authorized Claude Cowork Skill
(see CLAUDE_COWORK_INTEGRATION.md) and apply only the proposals a human reviewer
explicitly approves. Nothing here is written to the database unapproved, and Viper
never contacts Teams/Outlook/the network itself — it only reads JSON files the Skill
already wrote to a local `cowork_imports/incoming/` folder colocated with the active
database.
"""

import json
import os
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk

from db import get_session
from db.models import Case
from services.import_drafts import (
    DraftFile,
    apply_proposal,
    detect_duplicate,
    ensure_cowork_import_paths,
    finalize_draft,
    get_active_db_path,
    get_retention_days,
    purge_expired_drafts,
    scan_incoming_drafts,
)

DRAFT_COLUMNS = ("subject", "sender", "received_at", "proposals", "status")
DRAFT_HEADINGS = {
    "subject": "Subject",
    "sender": "Sender",
    "received_at": "Received",
    "proposals": "Proposals",
    "status": "Status",
}

PROPOSAL_COLUMNS = ("decision", "kind", "when", "preview", "confidence", "flag")
PROPOSAL_HEADINGS = {
    "decision": "Decision",
    "kind": "Kind",
    "when": "When",
    "preview": "Preview",
    "confidence": "Confidence",
    "flag": "Flag",
}


class CoworkImportTab(ttk.Frame):
    def __init__(self, master, case_id: int):
        super().__init__(master, padding=10)
        self.case_id = case_id
        self._drafts: list[DraftFile] = []
        self._selected_draft: DraftFile | None = None
        self._decisions: dict[int, dict] = {}
        self._incident_number: str | None = None

        self._build_layout()
        self.refresh()

    def _build_layout(self) -> None:
        info_row = ttk.Frame(self)
        info_row.pack(fill="x")
        self.info_label = ttk.Label(info_row, text="", wraplength=760, justify="left")
        self.info_label.pack(side="left", fill="x", expand=True)
        ttk.Button(info_row, text="Check for Imports", bootstyle="success", command=self.refresh).pack(
            side="right"
        )

        panes = ttk.Panedwindow(self, orient="vertical")
        panes.pack(fill="both", expand=True, pady=(8, 0))

        draft_frame = ttk.Labelframe(panes, text="Pending Drafts (this case)", padding=6)
        self.draft_tree = ttk.Treeview(
            draft_frame, columns=DRAFT_COLUMNS, show="headings", selectmode="browse", height=6
        )
        for col in DRAFT_COLUMNS:
            self.draft_tree.heading(col, text=DRAFT_HEADINGS[col])
            self.draft_tree.column(col, width=140, anchor="w")
        self.draft_tree.tag_configure("invalid", foreground="#ff4444")
        self.draft_tree.pack(fill="both", expand=True)
        self.draft_tree.bind("<<TreeviewSelect>>", self._on_select_draft)
        panes.add(draft_frame, weight=1)

        proposal_frame = ttk.Labelframe(panes, text="Proposals in Selected Draft", padding=6)
        self.proposal_tree = ttk.Treeview(
            proposal_frame, columns=PROPOSAL_COLUMNS, show="headings", selectmode="extended", height=8
        )
        for col in PROPOSAL_COLUMNS:
            self.proposal_tree.heading(col, text=PROPOSAL_HEADINGS[col])
            self.proposal_tree.column(col, width=110, anchor="w")
        self.proposal_tree.column("preview", width=260)
        self.proposal_tree.tag_configure("approved", foreground="#00ff00")
        self.proposal_tree.tag_configure("rejected", foreground="#6c757d")
        self.proposal_tree.pack(fill="both", expand=True)
        panes.add(proposal_frame, weight=2)

        button_row = ttk.Frame(self)
        button_row.pack(fill="x", pady=(8, 0))
        ttk.Button(
            button_row, text="Approve Selected", bootstyle="success",
            command=lambda: self._decide_selected("approved"),
        ).pack(side="left")
        ttk.Button(
            button_row, text="Reject Selected", bootstyle="danger-outline",
            command=lambda: self._decide_selected("rejected"),
        ).pack(side="left", padx=(8, 0))
        ttk.Button(button_row, text="Edit Selected...", command=self._edit_selected).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(
            button_row, text="Finalize Draft", bootstyle="info", command=self._finalize_selected_draft
        ).pack(side="right")

    # --- Loading ---------------------------------------------------------

    def refresh(self) -> None:
        with get_session() as session:
            case = session.get(Case, self.case_id)
            self._incident_number = case.incident_number if case else None

        self.draft_tree.delete(*self.draft_tree.get_children())
        self.proposal_tree.delete(*self.proposal_tree.get_children())
        self._selected_draft = None
        self._decisions = {}

        if not self._incident_number:
            self._drafts = []
            self.info_label.configure(
                text="Set an Incident Number on the Overview tab to enable Cowork import "
                "review — drafts are matched to a case by an exact incident number."
            )
            return

        try:
            db_path = get_active_db_path()
            paths = ensure_cowork_import_paths(db_path)
            purge_expired_drafts(paths)
            all_drafts = scan_incoming_drafts(paths)
        except Exception as exc:  # noqa: BLE001 - surface as a friendly status line
            self.info_label.configure(text=f"Could not scan for Cowork imports: {exc}")
            self._drafts = []
            return

        self._drafts = [
            draft for draft in all_drafts if draft.data and draft.data.get("incident_number") == self._incident_number
        ]
        self.info_label.configure(
            text=(
                f"Incident {self._incident_number} — watching {paths.incoming} "
                f"({len(self._drafts)} draft(s) matching this case; processed drafts are "
                f"retained {get_retention_days()} day(s))."
            )
        )
        for index, draft in enumerate(self._drafts):
            source = (draft.data or {}).get("source", {})
            proposals = (draft.data or {}).get("proposals", []) if draft.data else []
            status = "Invalid" if draft.errors else "Ready for review"
            self.draft_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    source.get("subject", ""),
                    source.get("sender", ""),
                    source.get("received_at", ""),
                    len(proposals),
                    status,
                ),
                tags=("invalid",) if draft.errors else (),
            )

    def _on_select_draft(self, _event=None) -> None:
        selection = self.draft_tree.selection()
        if not selection:
            return
        draft = self._drafts[int(selection[0])]
        self._selected_draft = draft
        self._decisions = {}
        self.proposal_tree.delete(*self.proposal_tree.get_children())

        if draft.errors:
            messagebox.showerror(
                "Invalid Draft",
                "This draft file failed validation and cannot be reviewed:\n\n" + "\n".join(draft.errors),
            )
            return

        proposals = draft.data.get("proposals", []) if draft.data else []
        with get_session() as session:
            for index, proposal in enumerate(proposals):
                duplicate = detect_duplicate(session, self.case_id, proposal)
                self._decisions[index] = {
                    "decision": "pending",
                    "proposal": dict(proposal),
                    "duplicate": duplicate,
                }
        self._render_proposals()

    def _render_proposals(self) -> None:
        self.proposal_tree.delete(*self.proposal_tree.get_children())
        for index, entry in sorted(self._decisions.items()):
            proposal = entry["proposal"]
            tag = entry["decision"] if entry["decision"] in ("approved", "rejected") else ()
            flag = "\u26a0 Possible duplicate" if entry["duplicate"] else ""
            self.proposal_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    entry["decision"].capitalize(),
                    proposal.get("kind", ""),
                    proposal.get("timestamp") or proposal.get("due_date") or "",
                    self._proposal_preview(proposal),
                    proposal.get("confidence", ""),
                    flag,
                ),
                tags=(tag,) if tag else (),
            )

    @staticmethod
    def _proposal_preview(proposal: dict) -> str:
        kind = proposal.get("kind")
        if kind == "timeline":
            return proposal.get("description", "")
        if kind == "communication_log":
            return f"{proposal.get('comm_type', '')}: {proposal.get('summary', '')}"
        if kind == "due_out":
            return proposal.get("task", "")
        return json.dumps(proposal)

    # --- Review actions ----------------------------------------------------

    def _decide_selected(self, decision: str) -> None:
        if not self._selected_draft:
            return
        selected = self.proposal_tree.selection()
        if not selected:
            messagebox.showinfo("No Proposals Selected", "Select one or more proposals first.")
            return
        for iid in selected:
            self._decisions[int(iid)]["decision"] = decision
        self._render_proposals()
        for iid in selected:
            self.proposal_tree.selection_add(iid)

    def _edit_selected(self) -> None:
        selected = self.proposal_tree.selection()
        if len(selected) != 1:
            messagebox.showinfo("Edit Proposal", "Select exactly one proposal to edit.")
            return
        index = int(selected[0])
        entry = self._decisions[index]

        def on_save(updated: dict) -> None:
            self._decisions[index]["proposal"] = updated
            with get_session() as session:
                self._decisions[index]["duplicate"] = detect_duplicate(session, self.case_id, updated)
            self._render_proposals()

        _ProposalEditDialog(self, entry["proposal"], on_save=on_save)

    def _finalize_selected_draft(self) -> None:
        if not self._selected_draft or not self._decisions:
            messagebox.showinfo("Finalize Draft", "Select a draft with proposals first.")
            return

        pending = [index for index, entry in self._decisions.items() if entry["decision"] == "pending"]
        if pending:
            if not messagebox.askyesno(
                "Unreviewed Proposals",
                f"{len(pending)} proposal(s) have not been explicitly approved or rejected. "
                "They will be treated as rejected. Continue?",
            ):
                return
            for index in pending:
                self._decisions[index]["decision"] = "rejected"

        approved_count = 0
        errors: list[str] = []
        with get_session() as session:
            for index, entry in self._decisions.items():
                if entry["decision"] != "approved":
                    continue
                try:
                    apply_proposal(session, self.case_id, entry["proposal"])
                    approved_count += 1
                except Exception as exc:  # noqa: BLE001 - keep reviewing, don't crash the tab
                    errors.append(f"Proposal {index}: {exc}")
                    entry["decision"] = "rejected"

        if errors:
            messagebox.showerror("Some Proposals Could Not Be Applied", "\n".join(errors))

        reviewer = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"
        decisions_payload = [
            {"index": index, "decision": entry["decision"], "kind": entry["proposal"].get("kind")}
            for index, entry in sorted(self._decisions.items())
        ]
        paths = ensure_cowork_import_paths(get_active_db_path())
        finalize_draft(self._selected_draft, paths, decisions_payload, reviewer)

        messagebox.showinfo(
            "Draft Finalized",
            f"Applied {approved_count} proposal(s) to this case. The draft file was moved into "
            "the approved/rejected archive folder.",
        )
        self.refresh()


class _ProposalEditDialog(ttk.Toplevel):
    """A small generic field editor for one proposal, before it's approved."""

    def __init__(self, master, proposal: dict, on_save):
        super().__init__(title="Edit Proposal", master=master, transient=master)
        self._proposal = dict(proposal)
        self._vars: dict[str, tk.StringVar] = {}
        self._on_save = on_save

        form = ttk.Frame(self, padding=10)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        row = 0
        for key, value in self._proposal.items():
            if key == "kind":
                continue
            ttk.Label(form, text=key.replace("_", " ").title()).grid(row=row, column=0, sticky="nw", pady=4)
            var = tk.StringVar(value="" if value is None else str(value))
            ttk.Entry(form, textvariable=var, width=55).grid(row=row, column=1, sticky="ew", pady=4)
            self._vars[key] = var
            row += 1

        button_row = ttk.Frame(self, padding=(10, 0, 10, 10))
        button_row.pack(fill="x")
        ttk.Button(button_row, text="Save", bootstyle="success", command=self._save).pack(side="right")
        ttk.Button(button_row, text="Cancel", command=self.destroy).pack(side="right", padx=(0, 8))

    def _save(self) -> None:
        updated = dict(self._proposal)
        for key, var in self._vars.items():
            text = var.get().strip()
            updated[key] = text or None
        self._on_save(updated)
        self.destroy()
