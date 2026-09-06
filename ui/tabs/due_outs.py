"""Due Outs tab — outstanding investigation tasks/action items for a case.

Mirrors the legacy DueOuts.jsx behavior: overdue, not-yet-completed tasks are
flagged in the list, completed tasks are visually de-emphasized, and otherwise a
task's priority (Critical/High/Medium/Low) colors the row, matching the legacy
getPriorityColor mapping.
"""

import tkinter as tk
from datetime import date, datetime

import ttkbootstrap as ttk

from db import get_session
from db.models import DueOut
from ui.constants import DUE_OUT_PRIORITIES, DUE_OUT_PRIORITY_COLORS, DUE_OUT_STATUSES
from ui.tabs.list_form_tab import ListFormTab
from ui.widgets import date_entry


class DueOutsTab(ListFormTab):
    columns = ("status", "task", "owner", "priority", "due_date")
    column_headings = {
        "status": "Status",
        "task": "Task",
        "owner": "Owner",
        "priority": "Priority",
        "due_date": "Due Date",
    }
    model = DueOut

    def __init__(self, master, case_id: int):
        super().__init__(master, case_id)
        self.tree.tag_configure("overdue", foreground="#e06c75")
        self.tree.tag_configure("completed", foreground="#6c757d")
        for priority, color in DUE_OUT_PRIORITY_COLORS.items():
            self.tree.tag_configure(f"priority_{priority}", foreground=color)

    def build_form(self, parent) -> None:
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(3, weight=1)

        ttk.Label(parent, text="Task*").grid(row=0, column=0, sticky="nw")
        self.task_text = ttk.Text(parent, width=60, height=2)
        self.task_text.grid(row=0, column=1, columnspan=3, sticky="ew")

        ttk.Label(parent, text="Owner").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.owner_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.owner_var).grid(row=1, column=1, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="Due Date").grid(
            row=1, column=2, sticky="w", padx=(12, 0), pady=(6, 0)
        )
        self.due_date_var = tk.StringVar()
        date_entry(parent, self.due_date_var, width=12).grid(
            row=1, column=3, sticky="w", pady=(6, 0)
        )

        ttk.Label(parent, text="Priority").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.priority_var = tk.StringVar(value=DUE_OUT_PRIORITIES[1])
        ttk.Combobox(
            parent,
            textvariable=self.priority_var,
            values=DUE_OUT_PRIORITIES,
            state="readonly",
            width=15,
        ).grid(row=2, column=1, sticky="w", pady=(6, 0))

        ttk.Label(parent, text="Status").grid(row=2, column=2, sticky="w", padx=(12, 0), pady=(6, 0))
        self.status_var = tk.StringVar(value=DUE_OUT_STATUSES[0])
        ttk.Combobox(
            parent, textvariable=self.status_var, values=DUE_OUT_STATUSES, state="readonly", width=15
        ).grid(row=2, column=3, sticky="w", pady=(6, 0))

        self.reset_form()

    def row_values(self, record: DueOut) -> tuple:
        return (
            record.status,
            record.task,
            record.owner or "",
            record.priority,
            record.due_date or "",
        )

    def load_form(self, record: DueOut) -> None:
        self.task_text.delete("1.0", tk.END)
        self.task_text.insert("1.0", record.task)
        self.owner_var.set(record.owner or "")
        self.due_date_var.set(record.due_date or "")
        self.priority_var.set(record.priority)
        self.status_var.set(record.status)

    def read_form(self) -> dict:
        task = self.task_text.get("1.0", tk.END).strip()
        if not task:
            raise ValueError("Task description is required.")
        due_date = self.due_date_var.get().strip()
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Due date must be in the format YYYY-MM-DD.")
        return {
            "task": task,
            "owner": self.owner_var.get().strip() or None,
            "due_date": due_date or None,
            "priority": self.priority_var.get(),
            "status": self.status_var.get(),
        }

    def reset_form(self) -> None:
        self.task_text.delete("1.0", tk.END)
        self.owner_var.set("")
        self.due_date_var.set("")
        self.priority_var.set(DUE_OUT_PRIORITIES[1])
        self.status_var.set(DUE_OUT_STATUSES[0])

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        today = date.today().isoformat()
        with get_session() as session:
            for record in self.query_all(session, self.case_id):
                if record.status == "Completed":
                    tags = ("completed",)
                elif record.due_date and record.due_date < today:
                    tags = ("overdue",)
                elif record.priority in DUE_OUT_PRIORITY_COLORS:
                    tags = (f"priority_{record.priority}",)
                else:
                    tags = ()
                self.tree.insert(
                    "", "end", iid=str(record.id), values=self.row_values(record), tags=tags
                )
