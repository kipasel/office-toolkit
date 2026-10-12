THEME_QSS = """
* {
    font-family: 'Segoe UI', Arial, sans-serif;
}

QMainWindow {
    background: #ffffff;
}

QListWidget {
    background: #f8f9fa;
    border: none;
    padding: 8px;
}

QListWidget::item {
    padding: 8px 12px;
    margin: 2px 4px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background: #1f4e79;
    color: #ffffff;
}

QPushButton {
    background: #1f4e79;
    color: #ffffff;
    border: none;
    padding: 6px 14px;
    border-radius: 4px;
}

QPushButton:hover {
    background: #2a5f99;
}

QPushButton:disabled {
    background: #adb5bd;
    color: #495057;
}
"""
