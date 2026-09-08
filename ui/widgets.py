"""Small shared custom widgets used across multiple tabs."""

from pathlib import Path
from tkinter import font as tkfont

import ttkbootstrap as ttk
import tkinter as tk


def date_entry(parent, textvariable, width=18) -> ttk.DateEntry:
    """A ttkbootstrap `DateEntry` (Entry + calendar-popup button) bound to
    `textvariable`, so it's a drop-in replacement for a plain `ttk.Entry` in
    existing StringVar-based forms — typing still works, and picking a date from
    the calendar populates the same variable.

    Dates are always rendered/parsed as `YYYY-MM-DD`, matching the format every
    other date field in this app already expects.
    """
    widget = ttk.DateEntry(parent, dateformat="%Y-%m-%d", width=width)
    widget.entry.configure(textvariable=textvariable)
    return widget


ASSETS_DIR = Path(__file__).parent / "assets"
APP_TITLE = "Bastion Command: Viper"

# Preferred title/banner font, in priority order. "Bahnschrift" ships with
# Windows 10/11 and has the condensed, functional look of military/government
# signage (DIN-style); "Impact"/"Arial Black" are near-universal bold fallbacks
# on systems where Bahnschrift isn't installed.
TITLE_FONT_CANDIDATES = ["Bahnschrift", "Impact", "Arial Black"]

_rook_image: tk.PhotoImage | None = None  # kept alive for the process lifetime
_app_icon_image: tk.PhotoImage | None = None  # kept alive for the process lifetime


def _title_font(size: int, weight: str = "bold") -> tuple:
    available = set(tkfont.families())
    for family in TITLE_FONT_CANDIDATES:
        if family in available:
            return (family, size, weight)
    return ("TkDefaultFont", size, weight)


def get_app_icon() -> tk.PhotoImage | None:
    """The rook icon at full resolution, suitable for `window.iconphoto()`."""
    global _app_icon_image
    if _app_icon_image is None:
        icon_path = ASSETS_DIR / "PO_Rook.png"
        if icon_path.exists():
            _app_icon_image = tk.PhotoImage(file=str(icon_path))
    return _app_icon_image


def build_app_header(parent, subtitle: str | None = None) -> ttk.Frame:
    """A banner with the Bastion Command rook icon + title text (and an optional
    subtitle, e.g. the current case name), for use at the top of the main window
    and case-detail windows — mirroring the legacy web app's persistent page
    header.
    """
    global _rook_image

    outer = ttk.Frame(parent)

    row = ttk.Frame(outer, padding=(12, 10))
    row.pack(fill="x")

    if _rook_image is None:
        icon_path = ASSETS_DIR / "PO_Rook.png"
        if icon_path.exists():
            image = tk.PhotoImage(file=str(icon_path))
            wanted_height = 44
            if image.height() > wanted_height:
                factor = max(1, round(image.height() / wanted_height))
                image = image.subsample(factor, factor)
            _rook_image = image

    if _rook_image is not None:
        ttk.Label(row, image=_rook_image).pack(side="left", padx=(0, 10))

    text_col = ttk.Frame(row)
    text_col.pack(side="left")
    ttk.Label(text_col, text=APP_TITLE, font=_title_font(20), bootstyle="danger").pack(anchor="w")
    if subtitle:
        ttk.Label(text_col, text=subtitle, font=_title_font(11, "normal"), bootstyle="secondary").pack(
            anchor="w"
        )

    ttk.Separator(outer, bootstyle="danger").pack(fill="x")
    return outer

