from PySide6.QtWidgets import QListWidget
from PySide6.QtCore import Signal


class Navigation(QListWidget):
    home_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.addItem("Beranda")
        self.currentRowChanged.connect(self._on_change)

    def _on_change(self, row: int):
        if row == 0:
            self.home_requested.emit()
