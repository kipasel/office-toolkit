from PySide6.QtWidgets import QMainWindow, QStackedWidget, QHBoxLayout, QWidget
from PySide6.QtCore import Qt

from office_toolkit.core.config import AppConfig
from office_toolkit.services.pdf.ui import PdfToolkitPage
from office_toolkit.services.pdf.advanced_ui import PdfAdvancedPage
from office_toolkit.services.qr.ui import QrToolkitPage
from .navigation import Navigation
from .dashboard import Dashboard


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.setWindowTitle("Office Toolkit")
        self.resize(1100, 700)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.nav = Navigation()
        self.stack = QStackedWidget()
        self.dashboard = Dashboard()
        self.pdf_page = PdfToolkitPage()
        self.pdf_advanced_page = PdfAdvancedPage()
        self.qr_page = QrToolkitPage()
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.pdf_page)
        self.stack.addWidget(self.pdf_advanced_page)
        self.stack.addWidget(self.qr_page)

        layout.addWidget(self.nav)
        layout.addWidget(self.stack, 1)

        self.setCentralWidget(central)
        self.nav.page_requested.connect(self._on_page)
        self.nav.setCurrentRow(0)

    def _on_page(self, index: int):
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
