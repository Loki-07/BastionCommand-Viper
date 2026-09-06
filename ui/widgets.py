"""Small shared custom widgets used across multiple tabs."""

import ttkbootstrap as ttk


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
