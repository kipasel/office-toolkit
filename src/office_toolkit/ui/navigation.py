"""Sidebar navigation: brand, page items, unavailable items, status footer.

Keeps the public ``setCurrentRow`` / ``currentRow`` API and the
``page_requested(int)`` signal so existing wiring and tests continue to work,
while presenting a Metro-styled grouped sidebar.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from office_toolkit import __version__
from office_toolkit.ui.styles import icons
from office_toolkit.ui.styles.tokens import Spacing

_ICON_COLOR = "#C7D2FE"

_PAGES = [
    ("Beranda", "home"),
    ("PDF", "pdf"),
    ("PDF Lanjutan", "pdf_advanced"),
    ("QR Code", "qr"),
    ("Gambar", "image"),
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

        section = QLabel("NAVIGASI")
        section.setObjectName("navSectionLabel")
        layout.addWidget(section)

        self.list = QListWidget()
        self.list.setObjectName("sidebar")
        self.list.setFrameShape(QListWidget.NoFrame)
        self.list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setSelectionMode(QListWidget.SingleSelection)
        for label, icon_name in _PAGES:
            item = QListWidgetItem(icons.icon(icon_name, _ICON_COLOR, 20), label)
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
        self.list.setCurrentRow(row)

    def currentRow(self) -> int:  # noqa: N802 (Qt-style API)
        return self.list.currentRow()

    def _on_change(self, row: int) -> None:
        if row >= 0:
            self.page_requested.emit(row)
