"""Sidebar navigation: brand, home button, page items, unavailable items, footer.

Keeps the public ``setCurrentRow`` / ``currentRow`` API and the
``page_requested(int)`` signal so existing wiring and tests continue to work,
while presenting a Metro-styled grouped sidebar. Beranda is a standalone button
above the grouped navigation; the remaining pages are listed without scrolling.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from office_toolkit import __version__
from office_toolkit.ui.styles import icons
from office_toolkit.ui.styles.tokens import Spacing

_HOME_ICON_COLOR = "#93C5FD"

_PAGES = [
    ("PDF", "pdf", "#FCA5A5"),
    ("PDF Lanjutan", "pdf_advanced", "#FDBA74"),
    ("QR Code", "qr", "#C4B5FD"),
    ("Gambar", "image", "#5EEAD4"),
]

_UNAVAILABLE = ["File & Dokumen", "Pengaturan"]


class Navigation(QWidget):
    page_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(242)
        self.setObjectName("navigation")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_brand())

        self.home_btn = QPushButton(icons.icon("home", _HOME_ICON_COLOR, 20), "Beranda")
        self.home_btn.setObjectName("navHomeButton")
        self.home_btn.setCheckable(True)
        self.home_btn.setCursor(Qt.PointingHandCursor)
        self.home_btn.setIconSize(QSize(20, 20))
        self.home_btn.setFocusPolicy(Qt.NoFocus)
        self.home_btn.setFixedHeight(44)
        self.home_btn.clicked.connect(self._on_home_clicked)
        layout.addWidget(self.home_btn)

        section = QLabel("NAVIGASI")
        section.setObjectName("navSectionLabel")
        layout.addWidget(section)

        self.list = QListWidget()
        self.list.setObjectName("sidebar")
        self.list.setFrameShape(QListWidget.NoFrame)
        self.list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setSelectionMode(QListWidget.SingleSelection)
        for label, icon_name, icon_color in _PAGES:
            item = QListWidgetItem(icons.icon(icon_name, icon_color, 20), label)
            item.setSizeHint(QSize(0, 42))
            self.list.addItem(item)
        self.list.setFixedHeight(len(_PAGES) * 42 + 12)
        self.list.currentRowChanged.connect(self._on_change)
        layout.addWidget(self.list)

        soon = QLabel("SEGERA HADIR")
        soon.setObjectName("navSectionLabel")
        layout.addWidget(soon)

        self.more = QListWidget()
        self.more.setObjectName("sidebarDisabled")
        self.more.setFrameShape(QListWidget.NoFrame)
        self.more.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.more.setFocusPolicy(Qt.NoFocus)
        for label in _UNAVAILABLE:
            item = QListWidgetItem(label)
            item.setSizeHint(QSize(0, 32))
            item.setFlags(Qt.NoItemFlags)
            self.more.addItem(item)
        self.more.setFixedHeight(len(_UNAVAILABLE) * 32 + 8)
        layout.addWidget(self.more)

        layout.addStretch()

        footer = QLabel(f"v{__version__}  ·  Offline  ·  Tanpa telemetry")
        footer.setObjectName("navFooter")
        footer.setWordWrap(True)
        layout.addWidget(footer)

        self.setCurrentRow(0)

    @staticmethod
    def _build_brand() -> QWidget:
        block = QWidget()
        block.setObjectName("brandBlock")
        row = QVBoxLayout(block)
        row.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.MD)
        row.setSpacing(Spacing.SM)

        top = QWidget()
        top_row = QHBoxLayout(top)
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(Spacing.MD)
        logo = QLabel()
        logo.setPixmap(icons.app_logo(36))
        logo.setFixedSize(36, 36)
        top_row.addWidget(logo)

        names = QVBoxLayout()
        names.setSpacing(0)
        title = QLabel("Office Toolkit")
        title.setObjectName("brandTitle")
        subtitle = QLabel("PRODUKTIVITAS OFFLINE")
        subtitle.setObjectName("brandSubtitle")
        names.addWidget(title)
        names.addWidget(subtitle)
        top_row.addLayout(names)
        top_row.addStretch()
        row.addWidget(top)
        return block

    # -- public API (kept for compatibility) -----------------------------
    def setCurrentRow(self, row: int) -> None:  # noqa: N802 (Qt-style API)
        if row <= 0:
            self._select_home()
        else:
            self.home_btn.setChecked(False)
            self.list.setCurrentRow(row - 1)

    def currentRow(self) -> int:  # noqa: N802 (Qt-style API)
        if self.home_btn.isChecked():
            return 0
        row = self.list.currentRow()
        return row + 1 if row >= 0 else -1

    def _select_home(self) -> None:
        changed = not self.home_btn.isChecked() or self.list.currentRow() != -1
        self.home_btn.setChecked(True)
        if self.list.currentRow() != -1:
            self.list.setCurrentRow(-1)
        if changed:
            self.page_requested.emit(0)

    def _on_home_clicked(self) -> None:
        self._select_home()

    def _on_change(self, row: int) -> None:
        if row < 0:
            return
        if self.home_btn.isChecked():
            self.home_btn.setChecked(False)
        self.page_requested.emit(row + 1)
