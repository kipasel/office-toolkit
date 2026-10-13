"""UI tests for the PDF Toolkit page (offscreen Qt)."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QPushButton, QTabWidget

from office_toolkit.core.config import AppConfig
from office_toolkit.core.job_manager import JobManager, JobResult
from office_toolkit.services.pdf.ui import PdfToolkitPage
from office_toolkit.ui.main_window import MainWindow


@pytest.fixture
def app():
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp


def test_pdf_page_has_six_tabs(app):
    page = PdfToolkitPage()
    assert page.objectName() == "pdfToolkitPage"
    tabs = page.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.count() == 6
    assert isinstance(page.job_manager, JobManager)


def test_main_window_navigates_to_pdf(app):
    win = MainWindow(AppConfig())
    assert win.stack.count() == 4
    win.nav.setCurrentRow(1)
    assert win.stack.currentIndex() == 1
    win.nav.setCurrentRow(2)
    assert win.stack.currentIndex() == 2
    win.nav.setCurrentRow(3)
    assert win.stack.currentIndex() == 3
    win.nav.setCurrentRow(0)
    assert win.stack.currentIndex() == 0
    win.close()


def test_run_dispatches_job_and_reports(app):
    page = PdfToolkitPage()
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

    assert holder.get("res") is not None
    assert holder["res"].success is True
    assert button.isEnabled() is True
