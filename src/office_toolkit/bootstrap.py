import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from office_toolkit.core.config import AppConfig, get_config
from office_toolkit.core.logging_config import setup_logging
from office_toolkit.ui.main_window import MainWindow


def bootstrap() -> QApplication:
    """Bootstrap application: config, logging, Qt app, main window.

    A strong reference to the main window is kept on the QApplication instance so the
    window is not garbage-collected after this function returns.
    """
    config = get_config()
    setup_logging(config)

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setApplicationName("Office Toolkit")
    app.setOrganizationName("OfficeToolkit")
    app.setApplicationDisplayName("Office Toolkit")

    window = MainWindow(config)
    window.show()
    app._main_window = window

    return app
