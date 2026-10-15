"""Top header bar: page title/description, global tool search, app status."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from office_toolkit.ui.styles import icons
from office_toolkit.ui.styles.tokens import Colors, Spacing


class Header(QFrame):
    search_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("appHeader")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.MD)
        layout.setSpacing(Spacing.LG)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.title = QLabel("Beranda")
        self.title.setObjectName("headerTitle")
        self.desc = QLabel("Semua alat Office Toolkit dalam satu tempat.")
        self.desc.setObjectName("headerDesc")
        text_col.addWidget(self.title)
        text_col.addWidget(self.desc)
        layout.addLayout(text_col)
        layout.addStretch()

        self.search = QLineEdit()
        self.search.setObjectName("searchInput")
        self.search.setPlaceholderText("Cari alat...  (mis. gabung, qr, resize)")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(icons.icon("search", Colors.TEXT_SECONDARY, 16), QLineEdit.LeadingPosition)
        self.search.textChanged.connect(self.search_changed)
        layout.addWidget(self.search, 0, Qt.AlignVCenter)

        self.status = QLabel("●  Offline  ·  Lokal")
        self.status.setObjectName("statusBadge")
        self.status.setToolTip("Aplikasi berjalan sepenuhnya offline tanpa telemetry.")
        layout.addWidget(self.status, 0, Qt.AlignVCenter)

    def set_page(self, title: str, description: str) -> None:
        self.title.setText(title)
        self.desc.setText(description)

    def set_search_text(self, text: str) -> None:
        self.search.setText(text)
