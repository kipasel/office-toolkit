"""Token-driven QSS theme for the Office Toolkit Metro UI.

``build_qss`` generates the whole stylesheet from :mod:`tokens` so colours and
metrics never drift between widgets. ``apply_theme`` installs it on the running
``QApplication`` together with the Fusion base style and the Metro font.
"""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from . import icons
from .tokens import Colors, Fonts, Radius, Spacing


def build_qss() -> str:
    c = Colors
    return f"""
* {{
    font-family: 'Segoe UI Variable', 'Segoe UI', Arial, sans-serif;
    font-size: {Fonts.BODY}px;
}}

QWidget {{
    color: {c.TEXT};
}}

QMainWindow, QDialog {{
    background: {c.BG};
}}

#contentArea {{
    background: {c.BG};
}}

/* ---- Header -------------------------------------------------------- */
#appHeader {{
    background: {c.SURFACE};
    border-bottom: 1px solid {c.DIVIDER};
}}
#headerTitle {{
    font-size: {Fonts.H1}px;
    font-weight: 700;
    color: {c.TEXT};
}}
#headerDesc {{
    color: {c.TEXT_SECONDARY};
    font-size: {Fonts.SMALL}px;
}}
#statusBadge {{
    background: #E6F4EC;
    color: {c.SUCCESS};
    border: 1px solid #C7E7D5;
    border-radius: {Radius.PILL}px;
    padding: 4px 12px;
    font-size: {Fonts.TINY}px;
    font-weight: 600;
}}

/* ---- Sidebar ------------------------------------------------------- */
#sidebar {{
    background: {c.DEEP_NAVY};
    border: none;
    outline: 0;
    padding: {Spacing.SM}px 0;
}}
#sidebar::item {{
    color: {c.NAVY_TEXT};
    padding: 11px 16px;
    margin: 2px 10px;
    border-radius: {Radius.MD}px;
}}
#sidebar::item:hover {{
    background: {c.NAVY_HOVER};
    color: {c.WHITE};
}}
#sidebar::item:selected {{
    background: {c.NAVY_ACTIVE};
    color: {c.WHITE};
    border-left: 3px solid {c.PRIMARY};
}}
#sidebarDisabled {{
    background: {c.DEEP_NAVY};
    border: none;
    outline: 0;
    padding: 0;
}}
#sidebarDisabled::item {{
    color: {c.NAVY_TEXT_MUTED};
    padding: 9px 18px;
    margin: 1px 10px;
}}
#sidebarDisabled::item:selected {{
    background: transparent;
    color: {c.NAVY_TEXT_MUTED};
}}
#brandTitle {{
    color: {c.WHITE};
    font-size: {Fonts.H2}px;
    font-weight: 700;
}}
#brandSubtitle {{
    color: {c.NAVY_TEXT_MUTED};
    font-size: {Fonts.TINY}px;
    letter-spacing: 1px;
}}
#brandBlock {{
    background: {c.DEEP_NAVY};
}}
#navSectionLabel {{
    color: {c.NAVY_TEXT_MUTED};
    font-size: {Fonts.TINY}px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 4px 20px;
}}
#navFooter {{
    color: {c.NAVY_TEXT_MUTED};
    font-size: {Fonts.TINY}px;
    padding: 10px 18px;
    border-top: 1px solid {c.NAVY_HOVER};
}}

/* ---- Page headers -------------------------------------------------- */
#pageTitle {{
    font-size: {Fonts.H1}px;
    font-weight: 700;
    color: {c.TEXT};
}}
#pageDesc {{
    color: {c.TEXT_SECONDARY};
    font-size: {Fonts.SMALL}px;
}}
#sectionTitle {{
    font-size: {Fonts.H3}px;
    font-weight: 700;
    color: {c.TEXT};
}}
#hintText {{
    color: {c.TEXT_SECONDARY};
}}
#warningText {{
    color: {c.WARNING};
    font-weight: 600;
}}
#errorText {{
    color: {c.ERROR};
    font-weight: 600;
}}
#previewBox {{
    border: 1px dashed {c.BORDER};
    border-radius: {Radius.LG}px;
    background: {c.SURFACE};
}}

/* ---- Dashboard tiles ---------------------------------------------- */
#metroTile {{
    border-radius: {Radius.LG}px;
    border: 1px solid transparent;
}}
#metroTile:focus {{
    border: 2px solid {c.WHITE};
}}
#tileTitle {{
    color: {c.WHITE};
    font-size: {Fonts.TILE}px;
    font-weight: 700;
    background: transparent;
}}
#tileDesc {{
    color: rgba(255, 255, 255, 0.86);
    font-size: {Fonts.TINY}px;
    background: transparent;
}}
#tileBadge {{
    color: {c.WHITE};
    background: rgba(0, 0, 0, 0.22);
    border-radius: {Radius.PILL}px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
}}
#emptyStateIcon {{
    background: transparent;
}}
#emptyStateTitle {{
    font-size: {Fonts.H3}px;
    font-weight: 700;
    color: {c.TEXT};
}}
#emptyStateDesc {{
    color: {c.TEXT_SECONDARY};
}}

/* ---- Buttons ------------------------------------------------------- */
QPushButton {{
    background: {c.PRIMARY};
    color: {c.WHITE};
    border: 1px solid {c.PRIMARY};
    padding: 7px 16px;
    border-radius: {Radius.MD}px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: {c.PRIMARY_HOVER};
    border-color: {c.PRIMARY_HOVER};
}}
QPushButton:pressed {{
    background: {c.PRIMARY_PRESSED};
    border-color: {c.PRIMARY_PRESSED};
}}
QPushButton:disabled {{
    background: #C6CFDD;
    border-color: #C6CFDD;
    color: #F4F6FA;
}}
QPushButton#secondaryButton {{
    background: {c.SURFACE};
    color: {c.TEXT};
    border: 1px solid {c.BORDER};
}}
QPushButton#secondaryButton:hover {{
    background: {c.SURFACE_ALT};
    border-color: #C3CCDA;
}}
QPushButton#secondaryButton:pressed {{
    background: {c.DIVIDER};
}}
QPushButton#dangerButton {{
    background: {c.ERROR};
    border-color: {c.ERROR};
    color: {c.WHITE};
}}
QPushButton#dangerButton:hover {{
    background: #B02E2E;
    border-color: #B02E2E;
}}
QPushButton#linkButton {{
    background: transparent;
    border: none;
    color: {c.PRIMARY};
    padding: 4px 6px;
}}

/* ---- Text inputs --------------------------------------------------- */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {c.SURFACE};
    border: 1px solid {c.BORDER};
    border-radius: {Radius.MD}px;
    padding: 6px 10px;
    color: {c.TEXT};
    selection-background-color: {c.PRIMARY};
    selection-color: {c.WHITE};
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {c.PRIMARY};
}}
QLineEdit:disabled, QPlainTextEdit:disabled, QSpinBox:disabled,
QDoubleSpinBox:disabled, QComboBox:disabled {{
    background: {c.SURFACE_ALT};
    color: {c.TEXT_MUTED};
}}
QLineEdit#searchInput {{
    padding-left: 32px;
    background: {c.SURFACE_ALT};
    border: 1px solid transparent;
    border-radius: {Radius.PILL}px;
    min-width: 220px;
}}
QLineEdit#searchInput:focus {{
    background: {c.SURFACE};
    border: 1px solid {c.PRIMARY};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background: {c.SURFACE};
    border: 1px solid {c.BORDER};
    border-radius: {Radius.SM}px;
    selection-background-color: {c.PRIMARY_SOFT};
    selection-color: {c.TEXT};
    outline: 0;
}}

/* ---- Tabs ---------------------------------------------------------- */
QTabWidget::pane {{
    border: 1px solid {c.DIVIDER};
    border-radius: {Radius.LG}px;
    background: {c.SURFACE};
    top: -1px;
    padding: {Spacing.MD}px;
}}
QTabBar::tab {{
    background: transparent;
    color: {c.TEXT_SECONDARY};
    padding: 9px 16px;
    margin-right: 4px;
    border-radius: {Radius.MD}px;
    font-weight: 600;
}}
QTabBar::tab:hover {{
    color: {c.TEXT};
    background: {c.SURFACE_ALT};
}}
QTabBar::tab:selected {{
    color: {c.PRIMARY};
    background: {c.SURFACE};
}}

/* ---- Progress ------------------------------------------------------ */
QProgressBar {{
    border: none;
    background: {c.SURFACE_ALT};
    border-radius: 6px;
    height: 10px;
    text-align: center;
    color: {c.TEXT_SECONDARY};
    font-size: {Fonts.TINY}px;
}}
QProgressBar::chunk {{
    background: {c.PRIMARY};
    border-radius: 6px;
}}

/* ---- Lists, checkboxes, radios ------------------------------------ */
QListWidget {{
    background: {c.SURFACE};
    border: 1px solid {c.DIVIDER};
    border-radius: {Radius.MD}px;
    padding: 4px;
    outline: 0;
}}
QListWidget::item {{
    padding: 7px 10px;
    border-radius: {Radius.SM}px;
}}
QListWidget::item:selected {{
    background: {c.PRIMARY_SOFT};
    color: {c.TEXT};
}}
QListWidget::item:hover {{
    background: {c.SURFACE_ALT};
}}
QCheckBox, QRadioButton {{
    spacing: 8px;
    color: {c.TEXT};
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
}}

/* ---- Scrollbars ---------------------------------------------------- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #C6CFDD;
    border-radius: 5px;
    min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{
    background: #A9B4C6;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: #C6CFDD;
    border-radius: 5px;
    min-width: 28px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
    width: 0;
}}
QScrollBar::add-page, QScrollBar::sub-page {{
    background: transparent;
}}

/* ---- Menus / tooltips / message boxes ------------------------------ */
QMenu {{
    background: {c.SURFACE};
    border: 1px solid {c.BORDER};
    border-radius: {Radius.MD}px;
    padding: 6px;
}}
QMenu::item {{
    padding: 6px 18px;
    border-radius: {Radius.SM}px;
}}
QMenu::item:selected {{
    background: {c.PRIMARY_SOFT};
}}
QToolTip {{
    background: {c.TEXT};
    color: {c.WHITE};
    border: none;
    padding: 5px 8px;
    border-radius: {Radius.SM}px;
}}
QMessageBox {{
    background: {c.SURFACE};
}}
"""


def apply_theme(app: QApplication) -> None:
    """Apply Fusion base style, font, stylesheet and window icon."""
    app.setStyle("Fusion")
    font = QFont("Segoe UI Variable", Fonts.BODY)
    if not QFont(font).exactMatch():
        font = QFont("Segoe UI", Fonts.BODY)
    app.setFont(font)
    app.setStyleSheet(build_qss())
    app.setWindowIcon(icons.app_icon(48))
