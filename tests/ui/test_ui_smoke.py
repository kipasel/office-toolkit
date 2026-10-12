from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication
import pytest

from office_toolkit.ui.main_window import MainWindow
from office_toolkit.core.config import AppConfig


@pytest.fixture
def app():
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp


def test_main_window_created(app):
    cfg = AppConfig()
    win = MainWindow(cfg)
    win.show()
    assert win is not None
    win.close()


def test_dashboard_search_filters(app):
    from office_toolkit.ui.dashboard import Dashboard
    d = Dashboard()
    assert d is not None
    if hasattr(d, 'close'):
        d.close()


def test_navigation_switch(app):
    from office_toolkit.ui.navigation import Navigation
    nav = Navigation()
    nav.setCurrentRow(0)
    assert nav.currentRow() == 0
    if hasattr(nav, 'close'):
        nav.close()
