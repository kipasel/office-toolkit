import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from office_toolkit.core.config import AppConfig, get_config
from office_toolkit.core.logging_config import setup_logging
from office_toolkit.ui.main_window import MainWindow


def bootstrap() -> QApplication:
    """Bootstrap application: config, logging, Qt app, main window."""
    config = get_config()
    setup_logging(config)

    app = QApplication(sys.argv)
    app.setApplicationName("Office Toolkit")
    app.setOrganizationName("OfficeToolkit")
    app.setApplicationDisplayName("Office Toolkit")

    window = MainWindow(config)
    window.show()

    return app
