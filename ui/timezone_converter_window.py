"""Time Zone Converter — a standalone utility (independent of any case) for converting
a date/time from one IANA time zone to several others at once, to help schedule calls
with stakeholders/experts across regions. Opened from the main window's toolbar.
"""

import tkinter as tk
import zoneinfo
from datetime import datetime
from tkinter import messagebox
from zoneinfo import ZoneInfo

import ttkbootstrap as ttk

ALL_TIMEZONES = sorted(zoneinfo.available_timezones())

# A short starter list of commonly-used zones, added to the target list by default so
# the window is immediately useful without having to search first.
DEFAULT_TARGET_ZONES = [
    "UTC",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "Europe/London",
]


class TimezoneConverterWindow(ttk.Toplevel):
    def __init__(self, master):
        super().__init__(title="Time Zone Converter", master=master, transient=master, size=(700, 550))

        container = ttk.Frame(self, padding=15)
        container.pack(fill="both", expand=True)
        container.columnconfigure(1, weight=1)

        # --- Source date/time/zone -----------------------------------------
        ttk.Label(container, text="Source Date/Time", font="-weight bold").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 6)
        )

        ttk.Label(container, text="Date (YYYY-MM-DD)").grid(row=1, column=0, sticky="w")
        now = datetime.now()
        self.date_var = tk.StringVar(value=now.strftime("%Y-%m-%d"))
        ttk.Entry(container, textvariable=self.date_var, width=14).grid(
            row=1, column=1, sticky="w", padx=(6, 12)
        )

        ttk.Label(container, text="Time (HH:MM, 24h)").grid(row=1, column=2, sticky="w")
        self.time_var = tk.StringVar(value=now.strftime("%H:%M"))
        ttk.Entry(container, textvariable=self.time_var, width=10).grid(
            row=1, column=3, sticky="w", padx=(6, 0)
        )

        ttk.Label(container, text="Source Time Zone").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.source_tz_var = tk.StringVar(value="UTC")
        self.source_tz_combo = ttk.Combobox(
            container, textvariable=self.source_tz_var, values=ALL_TIMEZONES, width=30
        )
        self.source_tz_combo.grid(row=2, column=1, columnspan=2, sticky="ew", pady=(6, 0))
        self.source_tz_combo.bind(
            "<KeyRelease>", lambda _event: self._filter_combo(self.source_tz_combo)
        )

        ttk.Button(container, text="Now", command=self._set_now).grid(
            row=2, column=3, sticky="w", padx=(6, 0), pady=(6, 0)
        )

        ttk.Button(
            container, text="Convert", bootstyle="success", command=self._convert
        ).grid(row=3, column=3, sticky="e", pady=(10, 10))

        # --- Add target zone -------------------------------------------------
        ttk.Label(container, text="Add Target Time Zone", font="-weight bold").grid(
            row=4, column=0, columnspan=4, sticky="w", pady=(0, 6)
        )
        self.add_tz_var = tk.StringVar()
        self.add_tz_combo = ttk.Combobox(
            container, textvariable=self.add_tz_var, values=ALL_TIMEZONES, width=30
        )
        self.add_tz_combo.grid(row=5, column=0, columnspan=3, sticky="ew")
        self.add_tz_combo.bind(
            "<KeyRelease>", lambda _event: self._filter_combo(self.add_tz_combo)
        )
        ttk.Button(container, text="Add", command=self._add_target_zone).grid(
            row=5, column=3, sticky="w", padx=(6, 0)
        )

        # --- Results tree ------------------------------------------------------
        results_frame = ttk.Frame(container)
        results_frame.grid(row=6, column=0, columnspan=4, sticky="nsew", pady=(10, 0))
        container.rowconfigure(6, weight=1)

        self.tree = ttk.Treeview(
            results_frame,
            columns=("timezone", "local_time", "offset", "day"),
            show="headings",
            height=10,
        )
        self.tree.heading("timezone", text="Time Zone")
        self.tree.heading("local_time", text="Local Date/Time")
        self.tree.heading("offset", text="UTC Offset")
        self.tree.heading("day", text="Day")
        self.tree.column("timezone", width=220, anchor="w")
        self.tree.column("local_time", width=170, anchor="w")
        self.tree.column("offset", width=100, anchor="w")
        self.tree.column("day", width=110, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(
            container, text="Remove Selected", bootstyle="danger-outline", command=self._remove_selected
        ).grid(row=7, column=0, sticky="w", pady=(8, 0))

        self.bind("<Escape>", lambda _event: self.destroy())

        self.target_zones: list[str] = list(DEFAULT_TARGET_ZONES)
        self._convert()

    def _filter_combo(self, combo: ttk.Combobox) -> None:
        typed = combo.get().strip().lower()
        combo["values"] = ALL_TIMEZONES if not typed else [
            tz for tz in ALL_TIMEZONES if typed in tz.lower()
        ]

    def _set_now(self) -> None:
        now = datetime.now()
        self.date_var.set(now.strftime("%Y-%m-%d"))
        self.time_var.set(now.strftime("%H:%M"))

    def _parse_source_datetime(self) -> datetime:
        date_str = self.date_var.get().strip()
        time_str = self.time_var.get().strip()
        tz_name = self.source_tz_var.get().strip()

        if tz_name not in ALL_TIMEZONES:
            raise ValueError(f"Unknown time zone: {tz_name!r}")

        try:
            naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError(
                "Enter date as YYYY-MM-DD and time as HH:MM (24-hour)."
            ) from None

        return naive.replace(tzinfo=ZoneInfo(tz_name))

    def _add_target_zone(self) -> None:
        tz_name = self.add_tz_var.get().strip()
        if not tz_name:
            return
        if tz_name not in ALL_TIMEZONES:
            messagebox.showerror("Unknown time zone", f"{tz_name!r} is not a recognized time zone.")
            return
        if tz_name not in self.target_zones:
            self.target_zones.append(tz_name)
        self.add_tz_var.set("")
        self._convert()

    def _remove_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No selection", "Select a row first.")
            return
        for iid in selection:
            values = self.tree.item(iid, "values")
            if values and values[0] in self.target_zones:
                self.target_zones.remove(values[0])
        self._convert()

    def _convert(self) -> None:
        try:
            source_dt = self._parse_source_datetime()
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self.tree.delete(*self.tree.get_children())
        for tz_name in self.target_zones:
            converted = source_dt.astimezone(ZoneInfo(tz_name))
            day_diff = (converted.date() - source_dt.date()).days
            if day_diff == 0:
                day_label = "Same day"
            elif day_diff > 0:
                day_label = f"+{day_diff} day" + ("s" if day_diff != 1 else "")
            else:
                day_label = f"{day_diff} day" + ("s" if day_diff != -1 else "")

            self.tree.insert(
                "",
                "end",
                values=(
                    tz_name,
                    converted.strftime("%Y-%m-%d %H:%M"),
                    converted.strftime("%z") or "+0000",
                    day_label,
                ),
            )
