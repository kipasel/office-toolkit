from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class Dashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("Office Toolkit - Dashboard")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)
        layout.addStretch()
