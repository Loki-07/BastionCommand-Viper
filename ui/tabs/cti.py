"""CTI tab — groups the three Cyber Threat Intelligence sub-features (PIRs, Running
Assessment, Intelligence Reports) into one case-detail tab via a nested Notebook.
"""

import ttkbootstrap as ttk

from ui.tabs.intelligence_report import IntelligenceReportTab
from ui.tabs.pir import PIRTab
from ui.tabs.running_assessment import RunningAssessmentTab


class CTITab(ttk.Frame):
    def __init__(self, master, case_id: int):
        super().__init__(master, padding=10)
        self.case_id = case_id

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        notebook.add(PIRTab(notebook, case_id), text="PIRs")
        notebook.add(RunningAssessmentTab(notebook, case_id), text="Running Assessment")
        notebook.add(IntelligenceReportTab(notebook, case_id), text="Intel Reports")
