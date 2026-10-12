from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
)


class FileSelector(QWidget):
    files_changed = Signal(list)

    def __init__(self, multi: bool = False, filter: str = "All Files (*.*)", parent=None):
        super().__init__(parent)
        self.multi = multi
        self.filter = filter
        self._files: List[Path] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.btn = QPushButton("Pilih File" if not multi else "Pilih File...")
        self.label = QLabel("Belum ada file dipilih")
        layout.addWidget(self.btn)
        layout.addWidget(self.label, 1)
        self.btn.clicked.connect(self._open)

    def _open(self):
        if self.multi:
            files, _ = QFileDialog.getOpenFileNames(self, "Pilih File", str(Path.cwd()), self.filter)
            if not files:
                return
            self._files = [Path(f) for f in files]
        else:
            f, _ = QFileDialog.getOpenFileName(self, "Pilih File", str(Path.cwd()), self.filter)
            if not f:
                return
            self._files = [Path(f)]
        self.label.setText(f"{len(self._files)} file dipilih")
        self.files_changed.emit(self._files)

    def files(self) -> List[Path]:
        return list(self._files)
