"""Metro-tile dashboard: grouped, searchable entry points to every tool.

Tiles are generated from :mod:`office_toolkit.ui.tools`; only tools that exist
in the specification are shown, unavailable tools are explicitly labelled, and
the search filters the real registry (never a decorative field).
"""

from __future__ import annotations

from typing import Dict, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from office_toolkit.ui.components.tile import MetroTile
from office_toolkit.ui.styles import icons
from office_toolkit.ui.styles.tokens import Colors, Spacing
from office_toolkit.ui.tools import CATEGORIES, TOOLS, Category, Tool, search_tools

_COLUMNS = 3


class _CategorySection(QWidget):
    def __init__(self, category: Category, parent=None):
        super().__init__(parent)
        self.category = category
        self.tiles: List[MetroTile] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, Spacing.SM)
        layout.setSpacing(Spacing.SM)

        head = QHBoxLayout()
        head.setSpacing(Spacing.SM)
        dot = QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(f"background: {category.color}; border-radius: 3px;")
        head.addWidget(dot)
        title = QLabel(category.title)
        title.setObjectName("sectionTitle")
        head.addWidget(title)
        head.addStretch()
        layout.addLayout(head)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(Spacing.MD)
        self.grid.setVerticalSpacing(Spacing.MD)
        layout.addLayout(self.grid)

    def add_tile(self, tool: Tool, on_click) -> MetroTile:
        tile = MetroTile(tool, self.category)
        tile.clicked.connect(on_click)
        row = len(self.tiles) // _COLUMNS
        col = len(self.tiles) % _COLUMNS
        self.grid.addWidget(tile, row, col)
        self.tiles.append(tile)
        return tile

    def apply_filter(self, visible_ids: set) -> bool:
        any_visible = False
        for tile in self.tiles:
            visible = tile.tool.id in visible_ids
            tile.setVisible(visible)
            if visible:
                any_visible = True
        self.setVisible(any_visible)
        return any_visible


class Dashboard(QWidget):
    tool_requested = Signal(int, int)  # page index, tab index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboard")
        self._sections: List[_CategorySection] = []
        self._tool_by_id: Dict[str, Tool] = {t.id: t for t in TOOLS}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(scroll)

        content = QWidget()
        content.setObjectName("contentArea")
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(
            Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XXL
        )
        self._content_layout.setSpacing(Spacing.XL)

        self._empty = self._build_empty_state()
        self._content_layout.addWidget(self._empty)
        self._empty.setVisible(False)

        tools_by_cat: Dict[str, List[Tool]] = {}
        for tool in TOOLS:
            tools_by_cat.setdefault(tool.category, []).append(tool)

        for category in CATEGORIES:
            section = _CategorySection(category)
            for tool in tools_by_cat.get(category.id, []):
                section.add_tile(tool, self._on_tile)
            self._sections.append(section)
            self._content_layout.addWidget(section)

        self._content_layout.addStretch()
        scroll.setWidget(content)

    @staticmethod
    def _build_empty_state() -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(Spacing.SM)
        icon = QLabel()
        icon.setObjectName("emptyStateIcon")
        icon.setPixmap(icons.pixmap("search", Colors.TEXT_MUTED, 56))
        icon.setAlignment(Qt.AlignCenter)
        title = QLabel("Tidak ada alat yang cocok")
        title.setObjectName("emptyStateTitle")
        title.setAlignment(Qt.AlignCenter)
        desc = QLabel("Coba kata kunci lain, misalnya “pdf”, “qr”, atau “gambar”.")
        desc.setObjectName("emptyStateDesc")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(desc)
        return w

    def _on_tile(self, tool: Tool) -> None:
        if tool.available and tool.page is not None and tool.tab is not None:
            self.tool_requested.emit(tool.page, tool.tab)

    def apply_filter(self, text: str) -> None:
        """Filter tiles by query; grouped sections hide when empty."""
        query = (text or "").strip()
        if not query:
            visible_ids = {t.id for t in TOOLS}
        else:
            visible_ids = {t.id for t in search_tools(query)}
        any_visible = False
        for section in self._sections:
            if section.apply_filter(visible_ids):
                any_visible = True
        self._empty.setVisible(not any_visible)
