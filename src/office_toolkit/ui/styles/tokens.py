"""Design tokens for the Office Toolkit Metro UI.

Single source of truth for colour, spacing, radius and typography. Widgets and
the generated QSS must read from here instead of hard-coding values, so the
visual language stays consistent across every page.
"""

from __future__ import annotations


class Colors:
    """Palette (Modern Metro + professional desktop)."""

    DEEP_NAVY = "#172554"
    NAVY_HOVER = "#1E3067"
    NAVY_ACTIVE = "#243B77"
    NAVY_TEXT = "#C7D2FE"
    NAVY_TEXT_MUTED = "#8FA2D6"

    PRIMARY = "#2563EB"
    PRIMARY_HOVER = "#1D4ED8"
    PRIMARY_PRESSED = "#1E40AF"
    PRIMARY_SOFT = "#DBEAFE"

    TEAL = "#0F9D8A"
    TEAL_DARK = "#0B7C6D"
    PURPLE = "#7657D5"
    PURPLE_DARK = "#5F44B5"
    ORANGE = "#E88A24"
    ORANGE_DARK = "#C4711A"
    GREEN = "#2E9D62"
    GREEN_DARK = "#237A4C"
    CORAL = "#E45B65"
    CORAL_DARK = "#C24650"

    BG = "#F4F6FA"
    SURFACE = "#FFFFFF"
    SURFACE_ALT = "#EEF2F8"

    TEXT = "#172033"
    TEXT_SECONDARY = "#687386"
    TEXT_MUTED = "#94A3B8"

    DIVIDER = "#E1E6EF"
    BORDER = "#DCE2EC"

    ERROR = "#C93636"
    WARNING = "#B7791F"
    SUCCESS = "#238653"
    WHITE = "#FFFFFF"


class Spacing:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


class Radius:
    SM = 6
    MD = 8
    LG = 12
    PILL = 999


class Fonts:
    FAMILY = "Segoe UI Variable, Segoe UI, Arial, sans-serif"
    H1 = 20
    H2 = 16
    H3 = 14
    TILE = 13
    BODY = 13
    SMALL = 12
    TINY = 11


CATEGORY_COLORS = {
    "beranda": Colors.PRIMARY,
    "pdf": Colors.CORAL,
    "qr": Colors.PURPLE,
    "gambar": Colors.TEAL,
    "file": Colors.ORANGE,
}
