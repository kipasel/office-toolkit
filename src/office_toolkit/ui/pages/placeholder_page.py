from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class PlaceholderPage(QWidget):
    def __init__(self, title: str, description: str = "Fitur ini akan diimplementasikan pada fase berikutnya.", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.title = QLabel(title)
        self.title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.desc = QLabel(description)
        layout.addWidget(self.title)
        layout.addWidget(self.desc)
        layout.addStretch()
