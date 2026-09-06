"""Root Cause Analysis (RCA) tab — one editable record per case, plus a simple
who/when audit trail (no full content snapshots — see `RCAHistoryEntry`).
"""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk

from db import RCAHistoryEntry, RootCauseAnalysis, get_session


class RCATab(ttk.Frame):
    def __init__(self, master, case_id: int):
        super().__init__(master, padding=15)
        self.case_id = case_id

        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Immediate Cause").grid(row=0, column=0, sticky="nw", pady=(0, 6))
        self.immediate_cause_text = ttk.Text(self, width=60, height=3)
        self.immediate_cause_text.grid(row=0, column=1, columnspan=3, sticky="ew", pady=(0, 6))

        ttk.Label(self, text="Contributing Factors").grid(
            row=1, column=0, sticky="nw", pady=(0, 6)
        )
        self.contributing_factors_text = ttk.Text(self, width=60, height=3)
        self.contributing_factors_text.grid(
            row=1, column=1, columnspan=3, sticky="ew", pady=(0, 6)
        )

        ttk.Label(self, text="Root Cause").grid(row=2, column=0, sticky="nw", pady=(0, 6))
        self.root_cause_text = ttk.Text(self, width=60, height=3)
        self.root_cause_text.grid(row=2, column=1, columnspan=3, sticky="ew", pady=(0, 6))

        ttk.Label(self, text="Timeline Refs (event IDs, comma-separated)").grid(
            row=3, column=0, sticky="w", pady=(0, 6)
        )
        self.timeline_refs_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.timeline_refs_var).grid(
            row=3, column=1, sticky="ew", pady=(0, 6)
        )

        ttk.Label(self, text="Author").grid(row=3, column=2, sticky="w", padx=(12, 0), pady=(0, 6))
        self.author_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.author_var, width=20).grid(
            row=3, column=3, sticky="w", pady=(0, 6)
        )

        self.status_label = ttk.Label(self, text="", bootstyle="secondary")
        self.status_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))

        ttk.Button(self, text="Save", bootstyle="success", command=self._save).grid(
            row=4, column=3, sticky="e", pady=(6, 0)
        )

        ttk.Label(self, text="Edit History", font="-weight bold").grid(
            row=5, column=0, columnspan=4, sticky="w", pady=(14, 4)
        )
        history_frame = ttk.Frame(self)
        history_frame.grid(row=6, column=0, columnspan=4, sticky="nsew")
        self.rowconfigure(6, weight=1)

        self.history_tree = ttk.Treeview(
            history_frame,
            columns=("version", "author", "timestamp"),
            show="headings",
            height=5,
        )
        self.history_tree.heading("version", text="Version")
        self.history_tree.heading("author", text="Author")
        self.history_tree.heading("timestamp", text="Timestamp")
        self.history_tree.column("version", width=70, anchor="w")
        self.history_tree.column("author", width=160, anchor="w")
        self.history_tree.column("timestamp", width=160, anchor="w")
        self.history_tree.pack(side="left", fill="both", expand=True)
        history_scroll = ttk.Scrollbar(
            history_frame, orient="vertical", command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=history_scroll.set)
        history_scroll.pack(side="right", fill="y")

        self._load()

    def _load(self) -> None:
        with get_session() as session:
            rca = session.query(RootCauseAnalysis).filter_by(case_id=self.case_id).first()
            if rca is not None:
                self.immediate_cause_text.delete("1.0", tk.END)
                self.immediate_cause_text.insert("1.0", rca.immediate_cause or "")
                self.contributing_factors_text.delete("1.0", tk.END)
                self.contributing_factors_text.insert("1.0", rca.contributing_factors or "")
                self.root_cause_text.delete("1.0", tk.END)
                self.root_cause_text.insert("1.0", rca.root_cause or "")
                self.timeline_refs_var.set(rca.timeline_refs or "")
                self.author_var.set(rca.author or "")
                self.status_label.configure(
                    text=(
                        f"Version {rca.version} — last updated "
                        f"{rca.updated_at.strftime('%Y-%m-%d %H:%M')}"
                    )
                )
            else:
                self.status_label.configure(text="No RCA yet for this case — save to create one.")

            history = (
                session.query(RCAHistoryEntry)
                .filter_by(case_id=self.case_id)
                .order_by(RCAHistoryEntry.timestamp.desc())
                .all()
            )
            self.history_tree.delete(*self.history_tree.get_children())
            for entry in history:
                self.history_tree.insert(
                    "",
                    "end",
                    iid=str(entry.id),
                    values=(
                        entry.version,
                        entry.author or "",
                        entry.timestamp.strftime("%Y-%m-%d %H:%M"),
                    ),
                )

    def _save(self) -> None:
        author = self.author_var.get().strip() or None
        data = {
            "immediate_cause": self.immediate_cause_text.get("1.0", tk.END).strip() or None,
            "contributing_factors": (
                self.contributing_factors_text.get("1.0", tk.END).strip() or None
            ),
            "root_cause": self.root_cause_text.get("1.0", tk.END).strip() or None,
            "timeline_refs": self.timeline_refs_var.get().strip() or None,
            "author": author,
        }

        try:
            with get_session() as session:
                rca = (
                    session.query(RootCauseAnalysis)
                    .filter_by(case_id=self.case_id)
                    .first()
                )
                if rca is None:
                    rca = RootCauseAnalysis(case_id=self.case_id, version=1, **data)
                    session.add(rca)
                else:
                    for key, value in data.items():
                        setattr(rca, key, value)
                    rca.version += 1
                session.flush()
                session.add(
                    RCAHistoryEntry(
                        case_id=self.case_id, version=rca.version, author=author
                    )
                )
        except Exception as exc:  # noqa: BLE001 - surface unexpected DB errors to the user
            messagebox.showerror("Save failed", f"Could not save this RCA:\n{exc}")
            return

        self._load()
        messagebox.showinfo("Saved", "Root cause analysis updated.")
