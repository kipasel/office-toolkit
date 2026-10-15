from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QFileDialog


class FolderSelector(QWidget):
    folder_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._folder: Optional[Path] = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.btn = QPushButton("Pilih Folder")
        self.btn.setObjectName("secondaryButton")
        self.label = QLabel("Belum ada folder dipilih")
        self.label.setObjectName("hintText")
        layout.addWidget(self.btn)
        layout.addWidget(self.label, 1)
        self.btn.clicked.connect(self._open)

    def _open(self):
        f = QFileDialog.getExistingDirectory(self, "Pilih Folder", str(Path.cwd()))
        if not f:
            return
        self._folder = Path(f)
        self.label.setText(str(self._folder))
        self.folder_changed.emit(self._folder)

    def folder(self) -> Optional[Path]:
        return self._folder
