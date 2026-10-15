from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from office_toolkit.core.config import AppConfig
from office_toolkit.services.pdf.ui import PdfToolkitPage
from office_toolkit.services.pdf.advanced_ui import PdfAdvancedPage
from office_toolkit.services.qr.ui import QrToolkitPage
from office_toolkit.services.images.ui import ImageToolkitPage
from office_toolkit.ui.components.header import Header
from .navigation import Navigation
from .dashboard import Dashboard

_PAGE_INFO = [
    ("Beranda", "Semua alat Office Toolkit dalam satu tempat. Pilih kartu untuk mulai."),
    ("PDF Toolkit", "Info, gabung, pisah, ekstrak, susun ulang, dan rotasi halaman PDF."),
    ("PDF Lanjutan", "Kompresi, PDF ↔ gambar, teks/gambar/anotasi/tanda tangan, proteksi."),
    ("QR Toolkit", "Buat QR, ekspor PNG/SVG, batch dari CSV, dan baca QR dari gambar."),
    ("Image Toolkit", "Info gambar, konversi format, dan ubah ukuran."),
]


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.setWindowTitle("Office Toolkit")
        self.resize(1180, 760)
        self.setMinimumSize(1000, 660)

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.nav = Navigation()

        right = QWidget()
        right.setObjectName("contentArea")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.header = Header()
        right_layout.addWidget(self.header)

        self.stack = QStackedWidget()
        self.dashboard = Dashboard()
        self.pdf_page = PdfToolkitPage()
        self.pdf_advanced_page = PdfAdvancedPage()
        self.qr_page = QrToolkitPage()
        self.image_page = ImageToolkitPage()
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.pdf_page)
        self.stack.addWidget(self.pdf_advanced_page)
        self.stack.addWidget(self.qr_page)
        self.stack.addWidget(self.image_page)
        right_layout.addWidget(self.stack, 1)

        root.addWidget(self.nav)
        root.addWidget(right, 1)

        self.setCentralWidget(central)
        self.nav.page_requested.connect(self._on_page)
        self.dashboard.tool_requested.connect(self._on_tool)
        self.header.search_changed.connect(self._on_search)
        self.nav.setCurrentRow(0)

    def _on_page(self, index: int) -> None:
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
        if 0 <= index < len(_PAGE_INFO):
            self.header.set_page(*_PAGE_INFO[index])

    def _on_tool(self, page: int, tab: int) -> None:
        if not (0 <= page < self.stack.count()):
            return
        self.nav.setCurrentRow(page)
        self.stack.setCurrentIndex(page)
        if 0 <= page < len(_PAGE_INFO):
            self.header.set_page(*_PAGE_INFO[page])
        page_widget = self.stack.widget(page)
        tabs = page_widget.findChild(QTabWidget)
        if tabs is not None and 0 <= tab < tabs.count():
            tabs.setCurrentIndex(tab)

    def _on_search(self, text: str) -> None:
        self.nav.setCurrentRow(0)
        self.stack.setCurrentIndex(0)
        if _PAGE_INFO:
            self.header.set_page(*_PAGE_INFO[0])
        self.dashboard.apply_filter(text)
