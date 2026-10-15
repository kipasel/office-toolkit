"""UI tests for the Image Toolkit page (offscreen Qt)."""

import time

import pytest
from PIL import Image
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QPushButton, QTabWidget

from office_toolkit.core.config import AppConfig
from office_toolkit.core.job_manager import JobManager, JobResult
from office_toolkit.services.images.ui import ImageToolkitPage
from office_toolkit.ui.main_window import MainWindow


@pytest.fixture
def app():
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp


def _wait(app, predicate, timeout_ms: int = 5000) -> bool:
    deadline = time.time() + timeout_ms / 1000.0
    while time.time() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(0.005)
    app.processEvents()
    return predicate()


def test_image_page_has_three_tabs(app):
    page = ImageToolkitPage()
    assert page.objectName() == "imageToolkitPage"
    tabs = page.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.count() == 3
    assert [tabs.tabText(i) for i in range(tabs.count())] == [
        "Info",
        "Konversi",
        "Resize",
    ]
    assert isinstance(page.job_manager, JobManager)


def test_main_window_reaches_image_page(app):
    win = MainWindow(AppConfig())
    assert win.stack.count() == 5
    assert win.stack.widget(4).objectName() == "imageToolkitPage"
    win.nav.setCurrentRow(4)
    assert win.stack.currentIndex() == 4
    win.close()


def test_run_dispatches_job(app):
    page = ImageToolkitPage()
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


def test_info_tab_reports_dimensions(app, tmp_path):
    src = tmp_path / "pic.png"
    Image.new("RGB", (40, 24), "green").save(src)
    page = ImageToolkitPage()
    tabs = page.findChild(QTabWidget)
    view = tabs.widget(0).findChild(QPlainTextEdit)
    page.info_selector._files = [src]
    page.info_selector.label.setText(str(src))

    for b in [b for b in page.findChildren(QPushButton) if b.text() == "Tampilkan Informasi"]:
        b.click()
    assert _wait(app, lambda: "Lebar           : 40 px" in view.toPlainText())
    assert "Tinggi          : 24 px" in view.toPlainText()


def test_convert_tab_writes_file(app, tmp_path):
    src = tmp_path / "src.png"
    Image.new("RGBA", (20, 10), (0, 0, 255, 128)).save(src)
    out_dir = tmp_path / "out"
    page = ImageToolkitPage()
    page.convert_selector._files = [src]
    page.convert_selector.label.setText(str(src))
    page.convert_format.setCurrentIndex(1)  # JPEG
    page.convert_out._folder = out_dir
    page.convert_out.label.setText(str(out_dir))

    for b in [b for b in page.findChildren(QPushButton) if b.text() == "Konversi Gambar"]:
        b.click()
    assert _wait(app, lambda: bool(list(out_dir.glob("src.jpg"))))
    assert list(out_dir.glob("src.jpg"))[0].stat().st_size > 0
