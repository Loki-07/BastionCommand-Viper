"""Case detail window — hosts the per-case feature tabs in a Notebook."""

import ttkbootstrap as ttk

from ui.tabs import (
    AARTab,
    AffectedSystemsTab,
    AffectedUsersTab,
    CommunicationLogTab,
    CTITab,
    DueOutsTab,
    IncidentPOCsTab,
    IOCsTab,
    OverviewTab,
    RCATab,
    ReportExportTab,
    TimelineTab,
)


class CaseDetailWindow(ttk.Toplevel):
    """A separate window showing the full detail (Overview/Timeline/etc.) for one case."""

    def __init__(self, master, case_id: int, case_name: str):
        super().__init__(title=f"Case: {case_name}", master=master, transient=master, size=(900, 600))
        self.case_id = case_id

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        notebook.add(OverviewTab(notebook, case_id), text="Overview")
        notebook.add(TimelineTab(notebook, case_id), text="Timeline")
        notebook.add(AffectedSystemsTab(notebook, case_id), text="Affected Systems")
        notebook.add(AffectedUsersTab(notebook, case_id), text="Affected Users")
        notebook.add(IOCsTab(notebook, case_id), text="IOCs")
        notebook.add(DueOutsTab(notebook, case_id), text="Due Outs")
        notebook.add(RCATab(notebook, case_id), text="RCA")
        notebook.add(IncidentPOCsTab(notebook, case_id), text="Stakeholders")
        notebook.add(AARTab(notebook, case_id), text="AAR")
        notebook.add(CommunicationLogTab(notebook, case_id), text="Comm Log")
        notebook.add(CTITab(notebook, case_id), text="CTI")
        notebook.add(ReportExportTab(notebook, case_id), text="Export")

        self.bind("<Escape>", lambda _event: self.destroy())

