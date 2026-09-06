"""After Action Review (AAR) tab — one editable record per case, plus a simple
who/when audit trail (same pattern as RCA — see `AARHistoryEntry`).

Participants and the lessons-learned Q&A are kept as free-form text rather than
structured JSON/dynamic rows (no Expert Finder or multi-user auth in this app yet).
The summary stats are recomputed and snapshotted into the record every time it's saved.
"""

import tkinter as tk
from datetime import datetime, timezone
from tkinter import messagebox

import ttkbootstrap as ttk

from db import (
    AARHistoryEntry,
    AffectedSystem,
    AffectedUser,
    AfterActionReview,
    Case,
    IOC,
    RootCauseAnalysis,
    TimelineEvent,
    get_session,
)
from ui.widgets import date_entry


def _compute_summary_stats(session, case_id: int) -> dict:
    """Recompute the auto-populated AAR fields from the case's current data."""
    case = session.get(Case, case_id)

    rca = session.query(RootCauseAnalysis).filter_by(case_id=case_id).first()
    rca_status = f"Draft (version {rca.version})" if rca is not None else "Not started"

    events = (
        session.query(TimelineEvent)
        .filter_by(case_id=case_id)
        .order_by(TimelineEvent.timestamp)
        .all()
    )
    if events:
        timeline_summary = (
            f"{len(events)} event(s) from {events[0].timestamp.strftime('%Y-%m-%d')} "
            f"to {events[-1].timestamp.strftime('%Y-%m-%d')}"
        )
    else:
        timeline_summary = "No timeline events recorded."

    ioc_count = session.query(IOC).filter_by(case_id=case_id).count()
    affected_systems_count = session.query(AffectedSystem).filter_by(case_id=case_id).count()
    affected_users_count = session.query(AffectedUser).filter_by(case_id=case_id).count()

    if case is not None:
        created_at = case.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - created_at
        case_duration = f"{delta.days} day(s)"
    else:
        case_duration = "Unknown"

    return {
        "rca_status": rca_status,
        "timeline_summary": timeline_summary,
        "ioc_count": ioc_count,
        "affected_systems_count": affected_systems_count,
        "affected_users_count": affected_users_count,
        "case_duration": case_duration,
    }


class AARTab(ttk.Frame):
    def __init__(self, master, case_id: int):
        super().__init__(master, padding=15)
        self.case_id = case_id

        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)

        ttk.Label(self, text="Review Date").grid(row=0, column=0, sticky="w")
        self.review_date_var = tk.StringVar()
        date_entry(self, self.review_date_var, width=12).grid(row=0, column=1, sticky="w")

        ttk.Label(self, text="Author").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.author_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.author_var, width=20).grid(row=0, column=3, sticky="w")

        ttk.Label(self, text="Participants (one per line)").grid(
            row=1, column=0, sticky="nw", pady=(6, 0)
        )
        self.participants_text = ttk.Text(self, width=60, height=3)
        self.participants_text.grid(row=1, column=1, columnspan=3, sticky="ew", pady=(6, 0))

        five_ws = ttk.Labelframe(self, text="5 W's", padding=8)
        five_ws.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        five_ws.columnconfigure(1, weight=1)
        five_ws.columnconfigure(3, weight=1)
        self.who_var = tk.StringVar()
        self.what_var = tk.StringVar()
        self.where_var = tk.StringVar()
        self.when_var = tk.StringVar()
        self.why_var = tk.StringVar()
        ttk.Label(five_ws, text="Who").grid(row=0, column=0, sticky="w")
        ttk.Entry(five_ws, textvariable=self.who_var).grid(row=0, column=1, sticky="ew")
        ttk.Label(five_ws, text="What").grid(row=0, column=2, sticky="w", padx=(12, 0))
        ttk.Entry(five_ws, textvariable=self.what_var).grid(row=0, column=3, sticky="ew")
        ttk.Label(five_ws, text="Where").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(five_ws, textvariable=self.where_var).grid(row=1, column=1, sticky="ew", pady=(6, 0))
        ttk.Label(five_ws, text="When").grid(row=1, column=2, sticky="w", padx=(12, 0), pady=(6, 0))
        ttk.Entry(five_ws, textvariable=self.when_var).grid(row=1, column=3, sticky="ew", pady=(6, 0))
        ttk.Label(five_ws, text="Why").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(five_ws, textvariable=self.why_var).grid(
            row=2, column=1, columnspan=3, sticky="ew", pady=(6, 0)
        )

        ttk.Label(self, text="Lessons Learned (Q&A)").grid(
            row=3, column=0, sticky="nw", pady=(10, 0)
        )
        self.qa_text = ttk.Text(self, width=60, height=4)
        self.qa_text.grid(row=3, column=1, columnspan=3, sticky="ew", pady=(10, 0))

        ttk.Label(self, text="Comments").grid(row=4, column=0, sticky="nw", pady=(6, 0))
        self.comments_text = ttk.Text(self, width=60, height=3)
        self.comments_text.grid(row=4, column=1, columnspan=3, sticky="ew", pady=(6, 0))

        ttk.Label(self, text="Improvement Notes").grid(row=5, column=0, sticky="nw", pady=(6, 0))
        self.improvement_notes_text = ttk.Text(self, width=60, height=3)
        self.improvement_notes_text.grid(row=5, column=1, columnspan=3, sticky="ew", pady=(6, 0))

        summary_frame = ttk.Labelframe(self, text="Auto-Computed Summary (snapshotted on save)", padding=8)
        summary_frame.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        self.summary_label = ttk.Label(summary_frame, text="", justify="left")
        self.summary_label.pack(anchor="w")

        self.status_label = ttk.Label(self, text="", bootstyle="secondary")
        self.status_label.grid(row=7, column=0, columnspan=2, sticky="w", pady=(6, 0))

        ttk.Button(self, text="Save", bootstyle="success", command=self._save).grid(
            row=7, column=3, sticky="e", pady=(6, 0)
        )

        ttk.Label(self, text="Edit History", font="-weight bold").grid(
            row=8, column=0, columnspan=4, sticky="w", pady=(14, 4)
        )
        history_frame = ttk.Frame(self)
        history_frame.grid(row=9, column=0, columnspan=4, sticky="nsew")
        self.rowconfigure(9, weight=1)

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
            aar = session.query(AfterActionReview).filter_by(case_id=self.case_id).first()
            if aar is not None:
                self.review_date_var.set(aar.review_date or "")
                self.author_var.set(aar.author or "")
                self.participants_text.delete("1.0", tk.END)
                self.participants_text.insert("1.0", aar.participants or "")
                self.who_var.set(aar.who or "")
                self.what_var.set(aar.what or "")
                self.where_var.set(aar.where or "")
                self.when_var.set(aar.when or "")
                self.why_var.set(aar.why or "")
                self.qa_text.delete("1.0", tk.END)
                self.qa_text.insert("1.0", aar.questions_and_answers or "")
                self.comments_text.delete("1.0", tk.END)
                self.comments_text.insert("1.0", aar.comments or "")
                self.improvement_notes_text.delete("1.0", tk.END)
                self.improvement_notes_text.insert("1.0", aar.improvement_notes or "")
                self.summary_label.configure(
                    text=(
                        f"RCA Status: {aar.rca_status}\n"
                        f"Timeline: {aar.timeline_summary}\n"
                        f"IOCs: {aar.ioc_count}    "
                        f"Affected Systems: {aar.affected_systems_count}    "
                        f"Affected Users: {aar.affected_users_count}\n"
                        f"Case Duration: {aar.case_duration}"
                    )
                )
                self.status_label.configure(
                    text=(
                        f"Version {aar.version} — last updated "
                        f"{aar.updated_at.strftime('%Y-%m-%d %H:%M')}"
                    )
                )
            else:
                stats = _compute_summary_stats(session, self.case_id)
                self.summary_label.configure(
                    text=(
                        f"RCA Status: {stats['rca_status']}\n"
                        f"Timeline: {stats['timeline_summary']}\n"
                        f"IOCs: {stats['ioc_count']}    "
                        f"Affected Systems: {stats['affected_systems_count']}    "
                        f"Affected Users: {stats['affected_users_count']}\n"
                        f"Case Duration: {stats['case_duration']}"
                    )
                )
                self.status_label.configure(text="No AAR yet for this case — save to create one.")

            history = (
                session.query(AARHistoryEntry)
                .filter_by(case_id=self.case_id)
                .order_by(AARHistoryEntry.timestamp.desc())
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
        review_date = self.review_date_var.get().strip()
        if review_date:
            try:
                datetime.strptime(review_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Invalid input", "Review date must be in the format YYYY-MM-DD.")
                return

        author = self.author_var.get().strip() or None
        data = {
            "review_date": review_date or None,
            "author": author,
            "participants": self.participants_text.get("1.0", tk.END).strip() or None,
            "who": self.who_var.get().strip() or None,
            "what": self.what_var.get().strip() or None,
            "where": self.where_var.get().strip() or None,
            "when": self.when_var.get().strip() or None,
            "why": self.why_var.get().strip() or None,
            "questions_and_answers": self.qa_text.get("1.0", tk.END).strip() or None,
            "comments": self.comments_text.get("1.0", tk.END).strip() or None,
            "improvement_notes": self.improvement_notes_text.get("1.0", tk.END).strip() or None,
        }

        try:
            with get_session() as session:
                stats = _compute_summary_stats(session, self.case_id)
                aar = (
                    session.query(AfterActionReview)
                    .filter_by(case_id=self.case_id)
                    .first()
                )
                if aar is None:
                    aar = AfterActionReview(case_id=self.case_id, version=1, **data, **stats)
                    session.add(aar)
                else:
                    for key, value in {**data, **stats}.items():
                        setattr(aar, key, value)
                    aar.version += 1
                session.flush()
                session.add(
                    AARHistoryEntry(case_id=self.case_id, version=aar.version, author=author)
                )
        except Exception as exc:  # noqa: BLE001 - surface unexpected DB errors to the user
            messagebox.showerror("Save failed", f"Could not save this AAR:\n{exc}")
            return

        self._load()
        messagebox.showinfo("Saved", "After Action Review updated.")
