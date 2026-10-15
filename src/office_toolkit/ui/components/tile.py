"""Metro tile widget used on the dashboard.

A tile is a coloured, keyboard-focusable card representing one registered tool.
Available tiles open their workspace; unavailable tiles are visually muted and
clearly labelled "BELUM TERSEDIA" and never pretend to do work.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from office_toolkit.ui.styles import icons
from office_toolkit.ui.styles.tokens import Colors, Radius, Spacing
from office_toolkit.ui.tools import Category, Tool

_MUTED_BG = "#E4E9F1"
_MUTED_BG_HOVER = "#DEE4EE"


class MetroTile(QFrame):
    clicked = Signal(object)  # emits the Tool

    def __init__(self, tool: Tool, category: Category, parent=None):
        super().__init__(parent)
        self.tool = tool
        self.category = category
        self.setObjectName("metroTile")
        self.setFixedHeight(118)
        self.setMinimumWidth(168)
        self.setProperty("available", tool.available)
        self.setAttribute(Qt.WA_Hover, True)

        label_color = Colors.WHITE if tool.available else Colors.TEXT_MUTED
        icon_color = Colors.WHITE if tool.available else "#A9B4C6"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        layout.setSpacing(Spacing.XS)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel()
        icon_label.setObjectName("tileIcon")
        icon_label.setPixmap(icons.pixmap(tool.icon, icon_color, 30))
        icon_label.setFixedSize(30, 30)
        top.addWidget(icon_label)
        top.addStretch()
        if not tool.available:
            badge = QLabel("BELUM TERSEDIA")
            badge.setObjectName("tileBadge")
            top.addWidget(badge, 0, Qt.AlignTop)
        layout.addLayout(top)
        layout.addStretch()

        title = QLabel(tool.name)
        title.setObjectName("tileTitle")
        title.setWordWrap(True)
        title.setStyleSheet(f"color: {label_color};")
        layout.addWidget(title)

        desc = QLabel(tool.description)
        desc.setObjectName("tileDesc")
        desc.setWordWrap(True)
        if not tool.available:
            desc.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        layout.addWidget(desc)

        if tool.available:
            self.setCursor(QCursor(Qt.PointingHandCursor))
            self.setFocusPolicy(Qt.StrongFocus)
            self.setStyleSheet(
                f"#metroTile {{ background: {category.color}; "
                f"border-radius: {Radius.LG}px; }}"
                f"#metroTile:hover {{ background: {self._darken(category.color)}; }}"
                f"#metroTile:focus {{ border: 2px solid {Colors.WHITE}; }}"
            )
            self.setToolTip(f"{tool.name} - {tool.description}")
        else:
            self.setFocusPolicy(Qt.NoFocus)
            self.setStyleSheet(
                f"#metroTile {{ background: {_MUTED_BG}; border-radius: {Radius.LG}px; }}"
                f"#metroTile:hover {{ background: {_MUTED_BG_HOVER}; }}"
            )
            self.setToolTip("Fitur ini belum tersedia.")

    @staticmethod
    def _darken(hex_color: str) -> str:
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        factor = 0.86
        return "#{:02X}{:02X}{:02X}".format(int(r * factor), int(g * factor), int(b * factor))

    # -- interaction -----------------------------------------------------
    def mouseReleaseEvent(self, event) -> None:
        if self.tool.available and event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit(self.tool)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if self.tool.available and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit(self.tool)
            return
        super().keyPressEvent(event)
