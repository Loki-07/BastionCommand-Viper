"""PIR (Priority Information Request) tab — the intelligence questions that need
answering to drive CTI collection during an investigation."""

import ttkbootstrap as ttk

from db.models import PIR
from ui.tabs.list_form_tab import ListFormTab


class PIRTab(ListFormTab):
    columns = ("created_at", "question")
    column_headings = {"created_at": "Created", "question": "Question"}
    model = PIR

    def build_form(self, parent) -> None:
        parent.columnconfigure(0, weight=1)

        ttk.Label(parent, text="Question*").grid(row=0, column=0, sticky="w")
        self.question_text = ttk.Text(parent, width=60, height=3)
        self.question_text.grid(row=1, column=0, sticky="ew", pady=(4, 0))

    def row_values(self, record: PIR) -> tuple:
        return (record.created_at.strftime("%Y-%m-%d %H:%M"), record.question)

    def load_form(self, record: PIR) -> None:
        self.question_text.delete("1.0", "end")
        self.question_text.insert("1.0", record.question)

    def read_form(self) -> dict:
        question = self.question_text.get("1.0", "end").strip()
        if not question:
            raise ValueError("Question is required.")
        return {"question": question}

    def reset_form(self) -> None:
        self.question_text.delete("1.0", "end")

    def query_all(self, session, case_id: int):
        return (
            session.query(PIR)
            .filter_by(case_id=case_id)
            .order_by(PIR.created_at)
            .all()
        )
