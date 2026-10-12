from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QComboBox,
    QSpinBox,
    QPushButton,
    QCheckBox,
    QLineEdit,
    QListWidget,
    QProgressBar,
    QMessageBox,
)

from office_toolkit.services.images import processor


class ImageToolkitPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("imageToolkitPage")
        layout = QVBoxLayout(self)
        title = QLabel("Image Toolkit")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        desc = QLabel("Konversi, resize, kompresi, crop, rotasi, dan batch processing (lokal/offline).")
        layout.addWidget(desc)
        layout.addStretch()
