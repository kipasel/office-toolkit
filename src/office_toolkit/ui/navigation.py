from PySide6.QtWidgets import QListWidget
from PySide6.QtCore import Signal


class Navigation(QListWidget):
    home_requested = Signal()
    page_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.addItem("Beranda")
        self.addItem("PDF Toolkit")
        self.addItem("PDF Lanjutan")
        self.addItem("QR Toolkit")
        self.currentRowChanged.connect(self._on_change)

    def _on_change(self, row: int):
        if row < 0:
            return
        if row == 0:
            self.home_requested.emit()
        self.page_requested.emit(row)
