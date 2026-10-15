"""UI tests for the PDF Lanjutan (advanced) page (offscreen Qt)."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QPushButton, QTabWidget

from office_toolkit.core.config import AppConfig
from office_toolkit.core.job_manager import JobManager, JobResult
from office_toolkit.services.pdf.advanced_ui import PdfAdvancedPage
from office_toolkit.ui.main_window import MainWindow


@pytest.fixture
def app():
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp


def test_advanced_page_has_nine_tabs(app):
    page = PdfAdvancedPage()
    assert page.objectName() == "pdfAdvancedPage"
    tabs = page.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.count() == 9
    assert isinstance(page.job_manager, JobManager)


def test_main_window_reaches_advanced_page(app):
    win = MainWindow(AppConfig())
    assert win.stack.count() == 5
    assert win.stack.widget(2).objectName() == "pdfAdvancedPage"
    win.nav.setCurrentRow(2)
    assert win.stack.currentIndex() == 2
    win.close()


def test_advanced_page_run_dispatches_job(app):
    page = PdfAdvancedPage()
    button = QPushButton()
    holder = {}
    loop = QEventLoop()

    def work() -> JobResult:
        return JobResult(success=True, data={"text": "ok"})

    def on_done(result: JobResult) -> None:
        holder["res"] = result
        loop.quit()

    page._run(button, work, on_done)
    assert button.isEnabled() is False
    QTimer.singleShot(10000, loop.quit)
    loop.exec()

    assert holder["res"].success is True
    assert button.isEnabled() is True