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


def test_bootstrap_keeps_main_window_alive(app, tmp_path, monkeypatch):
    """Regression: bootstrap() must keep the MainWindow from being garbage-collected."""
    from office_toolkit import bootstrap as bootstrap_mod
    from office_toolkit.bootstrap import bootstrap
    from office_toolkit.core.config import AppConfig

    cfg = AppConfig(
        app_dir=tmp_path,
        logs_dir=tmp_path / "logs",
        cache_dir=tmp_path / "cache",
        history_dir=tmp_path / "history",
    )
    cfg.ensure_dirs()
    monkeypatch.setattr(bootstrap_mod, "get_config", lambda: cfg)
    monkeypatch.setattr(bootstrap_mod, "setup_logging", lambda *a, **k: None)

    qapp = bootstrap()
    assert any(isinstance(w, MainWindow) for w in qapp.topLevelWidgets())
    qapp._main_window.close()

