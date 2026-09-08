"""Custom ttkbootstrap theme aligned with the legacy web app's
DESIGN_LANGUAGE_GUIDE.md color palette.

ttkbootstrap's stock "darkly" theme (used previously) is a generic dark theme
with its own muted blue/gray palette. This module registers a custom "bastion"
theme that maps ttkbootstrap's semantic color roles onto the exact hex values
documented in the legacy app's design guide, so every widget styled via the
built-in bootstyle roles (default buttons, `success`/`info`/`warning`/`danger`
variants, inputs, tabs, focus rings, etc.) automatically matches the original
web app's look without touching every individual tab file.

Color sourcing (see csim-app/DESIGN_LANGUAGE_GUIDE.md):
- bg / dark / border / inputbg: "Neutral Dark" (#0a0a0a), "Neutral Dark Accent"
  (#1a1a1a), and "Neutral Border" (#333333) from the Color Palette section.
- primary / success: "Success/Green" (#00ff00) — the guide uses green for every
  primary/call-to-action button (filled and outline), checkbox/radio accents,
  and input focus rings (see Interaction Patterns > Focus States).
- info: "Primary Blue" (#00d4ff) — used for links, important data cells, and
  informational text, distinct from the green action color.
- warning: "Warning/Orange" (#ffbb33); danger: "Danger/Red" (#ff4444).
- active (hover state): #222222, matching the guide's Row/Card Hover effects.
"""

from ttkbootstrap.style import ThemeDefinition

THEME_NAME = "bastion"

BASTION_COLORS = {
    "primary": "#00ff00",
    "secondary": "#888888",
    "success": "#00ff00",
    "info": "#00d4ff",
    "warning": "#ffbb33",
    "danger": "#ff4444",
    "light": "#cccccc",
    "dark": "#1a1a1a",
    "bg": "#0a0a0a",
    "fg": "#ffffff",
    "selectbg": "#264d3e",
    "selectfg": "#ffffff",
    "border": "#333333",
    "inputfg": "#ffffff",
    "inputbg": "#1a1a1a",
    "active": "#222222",
}


def apply_bastion_theme(window) -> None:
    """Register (once) and switch to the "bastion" theme on an existing window.

    Must be called AFTER the `ttkbootstrap.Window` is constructed (with any
    built-in placeholder theme, e.g. "darkly") rather than passed as the
    window's initial `themename`. Registering the theme via a standalone
    `Style()` call before any Tk root exists causes tkinter to silently create
    a separate hidden default root, which then breaks `iconphoto()` and other
    resources tied to the "real" window. Switching themes on the already-
    constructed window's own `Style` instance avoids that pitfall.
    """
    style = window.style
    if THEME_NAME not in style.theme_names():
        style.register_theme(
            ThemeDefinition(name=THEME_NAME, themetype="dark", colors=BASTION_COLORS)
        )
    style.theme_use(THEME_NAME)
    _use_dark_text_on_accent_colors(style)


def _use_dark_text_on_accent_colors(style) -> None:
    """Make button/toggle text black instead of white on bastion's accent colors.

    ttkbootstrap resolves button/checkbutton/radiobutton text color for every
    non-"light"/"dark" bootstyle (default, success, info, warning, danger,
    secondary) to `colors.selectfg`, which this theme keeps white so that
    Entry/Treeview text-selection highlighting (drawn against the much darker
    `selectbg`) stays readable. But bastion's accent colors themselves
    (`#00ff00` green, `#00d4ff` blue, `#ffbb33` orange, `#ff4444` red) are all
    bright, so white button text on them is hard to read. This overrides just
    that resolution (`Colors.get_foreground`) for the bastion theme's `Colors`
    instance so buttons/toggles get black text while text-selection foreground
    is untouched.
    """
    colors = style.colors
    original_get_foreground = colors.get_foreground

    def _get_foreground(color_label):
        if color_label in ("light", "dark"):
            return original_get_foreground(color_label)
        return "#000000"

    colors.get_foreground = _get_foreground

