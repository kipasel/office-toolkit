"""UI tests for the QR Toolkit page (offscreen Qt)."""

import time

import pytest
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QPushButton, QTabWidget

from office_toolkit.core.config import AppConfig
from office_toolkit.services.qr.ui import QrToolkitPage
from office_toolkit.ui.main_window import MainWindow
from fixtures.qr_factory import make_csv, make_qr_image


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


def test_qr_page_has_three_tabs(app):
    page = QrToolkitPage()
    assert page.objectName() == "qrPage"
    tabs = page.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.count() == 3
    assert [tabs.tabText(i) for i in range(tabs.count())] == [
        "Buat QR",
        "Batch dari CSV",
        "Baca QR",
    ]


def test_main_window_qr_navigation(app):
    win = MainWindow(AppConfig())
    assert win.stack.count() == 5
    assert win.stack.widget(3).objectName() == "qrPage"
    win.nav.setCurrentRow(3)
    assert win.stack.currentIndex() == 3
    win.close()


def test_gen_preview_shows_real_pixmap(app):
    page = QrToolkitPage()
    page.gen_data.setPlainText("PRATINJAU-152")
    page._refresh_gen_preview()
    pix = page.gen_preview.pixmap()
    assert pix is not None
    assert pix.isNull() is False


def test_gen_preview_clears_on_invalid_data(app):
    page = QrToolkitPage()
    page.gen_data.setPlainText("   ")
    page._refresh_gen_preview()
    assert page.gen_warn.text() != ""
    assert page.gen_preview.pixmap() is None or page.gen_preview.pixmap().isNull()


def test_export_png_button_writes_file(app, tmp_path):
    page = QrToolkitPage()
    page.gen_data.setPlainText("VALUE-7781")
    page.gen_out._folder = tmp_path
    page.gen_out.label.setText(str(tmp_path))
    page.gen_png_btn.click()

    def done() -> bool:
        text = page.gen_result.toPlainText()
        return "QR tersimpan" in text and bool(list(tmp_path.glob("qrcode.png")))

    assert _wait(app, done)
    files = list(tmp_path.glob("qrcode.png"))
    assert files and files[0].stat().st_size > 0


def test_export_requires_folder(app):
    page = QrToolkitPage()
    page.gen_data.setPlainText("X-1")
    page.gen_png_btn.click()

    def done() -> bool:
        return page.gen_png_btn.isEnabled()

    assert _wait(app, done)
    assert "Pilih folder tujuan" in page.gen_result.toPlainText()


def test_batch_tab_picks_columns_and_runs(app, tmp_path):
    csv_path = make_csv(
        tmp_path / "m.csv",
        ["isi", "nama"],
        [["Data-1", "satu"], ["Data-2", "dua"]],
    )
    out_dir = tmp_path / "out"
    page = QrToolkitPage()
    tabs = page.findChild(QTabWidget)
    tabs.setCurrentIndex(1)
    page.csv_selector._files = [csv_path]
    page.csv_selector.label.setText(str(csv_path))
    page.csv_selector.files_changed.emit(page.csv_selector.files())
    assert page.csv_content.count() == 2
    page.csv_out._folder = out_dir
    page.csv_out.label.setText(str(out_dir))

    for b in [b for b in page.findChildren(QPushButton) if b.text() == "Buat QR Massal"]:
        b.click()
    assert _wait(app, lambda: "Berhasil dibuat  : 2" in page.csv_result.toPlainText())
    assert len(list(out_dir.glob("*.png"))) == 2


def test_decode_tab_reports_payload(app, tmp_path):
    img = make_qr_image(tmp_path / "q.png", "ISI-UI-99")
    page = QrToolkitPage()
    tabs = page.findChild(QTabWidget)
    tabs.setCurrentIndex(2)
    page.dec_selector._files = [img]
    page.dec_selector.label.setText(str(img))
    page.dec_selector.files_changed.emit(page.dec_selector.files())

    for b in [b for b in page.findChildren(QPushButton) if b.text() == "Baca QR"]:
        b.click()
    assert _wait(app, lambda: page.dec_result.toPlainText() != "")
    assert "ISI-UI-99" in page.dec_result.toPlainText()