"""Report Export tab — assembles the full case record into JSON/Markdown/Text, shows a
live preview, and lets the user copy it to the clipboard or save it to a file. Intended
as a quick way to hand a case off to an AI assistant for report writing (per user
request) — this is a read-only export, it never modifies case data.
"""

import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk

from db import get_session
from ui.report_export import (
    format_as_json,
    format_as_markdown,
    format_as_text,
    gather_case_report,
)

_FORMATS = {
    "Markdown": (format_as_markdown, ".md", [("Markdown files", "*.md")]),
    "JSON": (format_as_json, ".json", [("JSON files", "*.json")]),
    "Text": (format_as_text, ".txt", [("Text files", "*.txt")]),
}


class ReportExportTab(ttk.Frame):
    def __init__(self, master, case_id: int):
        super().__init__(master, padding=15)
        self.case_id = case_id
        self._current_content = ""

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(toolbar, text="Format").pack(side="left", padx=(0, 6))
        self.format_var = tk.StringVar(value="Markdown")
        format_combo = ttk.Combobox(
            toolbar,
            textvariable=self.format_var,
            values=list(_FORMATS.keys()),
            state="readonly",
            width=12,
        )
        format_combo.pack(side="left", padx=(0, 12))
        format_combo.bind("<<ComboboxSelected>>", lambda _event: self._refresh())

        ttk.Button(toolbar, text="Refresh Preview", command=self._refresh).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(
            toolbar, text="Copy to Clipboard", bootstyle="secondary", command=self._copy
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            toolbar, text="Save to File...", bootstyle="success", command=self._save
        ).pack(side="left")

        preview_frame = ttk.Frame(self)
        preview_frame.grid(row=1, column=0, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.preview_text = tk.Text(preview_frame, wrap="word", state="disabled")
        self.preview_text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.preview_text.configure(yscrollcommand=scroll.set)

        self._refresh()

    def _refresh(self) -> None:
        try:
            with get_session() as session:
                data = gather_case_report(session, self.case_id)
        except Exception as exc:  # noqa: BLE001 - surface unexpected DB errors to the user
            messagebox.showerror("Export failed", f"Could not gather case data:\n{exc}")
            return

        formatter, _ext, _filetypes = _FORMATS[self.format_var.get()]
        content = formatter(data)
        self._current_content = content

        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", content)
        self.preview_text.configure(state="disabled")

    def _copy(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self._current_content)
        messagebox.showinfo("Copied", "Report copied to clipboard.")

    def _save(self) -> None:
        _formatter, ext, filetypes = _FORMATS[self.format_var.get()]
        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=filetypes + [("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._current_content)
        except OSError as exc:
            messagebox.showerror("Export failed", f"Could not write file:\n{exc}")
            return
        messagebox.showinfo("Exported", f"Report exported to:\n{path}")
