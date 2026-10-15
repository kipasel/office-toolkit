"""UI tests for the Metro redesign: tiles, search, sidebar (offscreen Qt)."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from office_toolkit.core.config import AppConfig
from office_toolkit.ui.components.tile import MetroTile
from office_toolkit.ui.dashboard import Dashboard
from office_toolkit.ui.main_window import MainWindow
from office_toolkit.ui.tools import TOOLS, search_tools


@pytest.fixture
def app():
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp


def test_every_registered_tool_has_a_tile(app):
    d = Dashboard()
    tiles = d.findChildren(MetroTile)
    assert len(tiles) == len(TOOLS)
    assert {t.tool.id for t in tiles} == {t.id for t in TOOLS}


def test_available_tools_point_to_a_real_workspace(app):
    for tool in TOOLS:
        if tool.available:
            assert tool.page is not None and tool.tab is not None
        else:
            assert tool.page is None and tool.tab is None


def test_filter_shows_only_matching_tiles(app):
    d = Dashboard()
    d.show()
    d.apply_filter("qr")
    visible = {t.tool.id for t in d.findChildren(MetroTile) if t.isVisible()}
    assert visible == {t.id for t in search_tools("qr")}
    assert visible  # non-empty
    base = {t.id for t in search_tools("qr")}
    assert "gabung_pdf" not in base


def test_filter_without_match_shows_empty_state(app):
    d = Dashboard()
    d.show()
    d.apply_filter("zzzz-tidak-ada")
    assert d._empty.isVisible()
    assert not any(t.isVisible() for t in d.findChildren(MetroTile))
    d.apply_filter("")
    assert not d._empty.isVisible()


def test_tile_click_emits_page_and_tab(app):
    d = Dashboard()
    received = {}
    d.tool_requested.connect(lambda p, t: received.update(page=p, tab=t))
    tool = next(t for t in TOOLS if t.id == "gabung_pdf")
    tile = next(x for x in d.findChildren(MetroTile) if x.tool.id == "gabung_pdf")
    tile.clicked.emit(tool)
    assert received == {"page": 1, "tab": 1}


def test_unavailable_tile_is_not_clickable(app):
    d = Dashboard()
    received = {}
    d.tool_requested.connect(lambda p, t: received.update(page=p, tab=t))
    tool = next(t for t in TOOLS if not t.available)
    tile = next(x for x in d.findChildren(MetroTile) if x.tool.id == tool.id)
    tile.clicked.emit(tool)
    assert received == {}
    assert tile.focusPolicy() == Qt.NoFocus


def test_sidebar_lists_pages_and_disabled_items(app):
    win = MainWindow(AppConfig())
    assert win.nav.list.count() == 5
    assert win.nav.more.count() == 2
    blocked = win.nav.more.item(0)
    assert not (blocked.flags() & Qt.ItemIsEnabled)
    win.close()


def test_header_search_switches_to_dashboard(app):
    win = MainWindow(AppConfig())
    win.show()
    win.nav.setCurrentRow(1)
    assert win.stack.currentIndex() == 1
    win.header.search.setText("qr")
    assert win.stack.currentIndex() == 0
    assert win.nav.currentRow() == 0
    visible = {t.tool.id for t in win.dashboard.findChildren(MetroTile) if t.isVisible()}
    assert visible == {t.id for t in search_tools("qr")}
    win.close()


def test_window_icon_is_set(app):
    from office_toolkit.ui.styles import icons

    assert not icons.app_icon(32).isNull()
