"""Image Toolkit UI page: info, format conversion, and resize.

Modul B (B1/B2/B9) — the page reuses the Phase 2 ``processor`` helpers and
follows the PDF/QR page conventions: Indonesian labels, the shared
``FileSelector``/``FolderSelector`` components, and heavy work executed on the
Qt worker via ``JobManager`` (the UI thread never processes files directly).

Only features with a real, tested implementation are exposed here; the rest of
Modul B remains explicitly out of scope until implemented.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from office_toolkit.core.errors import ProcessingError, ValidationError
from office_toolkit.core.job_manager import JobManager, JobResult
from office_toolkit.services.images import processor
from office_toolkit.ui.components.file_selector import FileSelector
from office_toolkit.ui.components.folder_selector import FolderSelector

_IMAGE_FILTER = "Gambar (*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tiff;*.tif)"

_CONVERT_FORMATS = [
    ("PNG", "png"),
    ("JPEG (.jpg)", "jpg"),
    ("WEBP", "webp"),
    ("BMP", "bmp"),
    ("TIFF", "tiff"),
]

_RESIZE_FORMATS = [
    ("PNG", "png"),
    ("JPEG (.jpg)", "jpg"),
    ("WEBP", "webp"),
]


def _result_view() -> QPlainTextEdit:
    view = QPlainTextEdit()
    view.setReadOnly(True)
    view.setPlaceholderText("Hasil akan ditampilkan di sini.")
    view.setMinimumHeight(70)
    return view


def _show(view: QPlainTextEdit, text: str, ok: bool) -> None:
    view.setPlainText(("" if ok else "[GAGAL] ") + text)


def _savings_text(savings_pct: float) -> str:
    if savings_pct >= 0:
        return f"Penghematan ukuran: {savings_pct:.1f}%"
    return f"Ukuran bertambah: {abs(savings_pct):.1f}% (hasil lebih besar dari sumber)"


class ImageToolkitPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("imageToolkitPage")
        self.job_manager = JobManager()
        self.job_manager.job_finished.connect(self._on_job_finished)
        self._callbacks: Dict[str, Callable[[JobResult], None]] = {}

        layout = QVBoxLayout(self)
        title = QLabel("Image Toolkit")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        desc = QLabel(
            "Informasi gambar, konversi format, dan ubah ukuran (lokal/offline)."
        )
        desc.setObjectName("pageDesc")
        layout.addWidget(desc)

        tabs = QTabWidget()
        tabs.addTab(self._build_info_tab(), "Info")
        tabs.addTab(self._build_convert_tab(), "Konversi")
        tabs.addTab(self._build_resize_tab(), "Resize")
        layout.addWidget(tabs, 1)

    # -- job plumbing -----------------------------------------------------
    def _run(
        self,
        button: QPushButton,
        func: Callable[[], JobResult],
        on_done: Callable[[JobResult], None],
    ) -> None:
        button.setEnabled(False)
        jid = self.job_manager.start_job(func)

        def wrapped(result: JobResult) -> None:
            button.setEnabled(True)
            on_done(result)

        self._callbacks[jid] = wrapped

    def _on_job_finished(self, jid: str, result: JobResult) -> None:
        cb = self._callbacks.pop(jid, None)
        if cb is not None:
            cb(result)

    # -- tabs -------------------------------------------------------------
    def _build_info_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.info_selector = FileSelector(multi=False, filter=_IMAGE_FILTER)
        v.addWidget(self.info_selector)
        btn = QPushButton("Tampilkan Informasi")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def work() -> JobResult:
            files = self.info_selector.files()
            if not files:
                return JobResult(success=False, error="Pilih satu file gambar terlebih dahulu.")
            try:
                info = processor.get_info(files[0])
            except (ValidationError, ProcessingError) as e:
                return JobResult(success=False, error=str(e))
            lines = [
                f"Nama file       : {info.path.name}",
                f"Lokasi          : {info.path}",
                f"Format          : {info.format or 'Tidak tersedia'}",
                f"Lebar           : {info.width} px",
                f"Tinggi          : {info.height} px",
                f"Ukuran file     : {info.size_bytes} byte",
                f"Transparansi    : {'Ya' if info.has_transparency else 'Tidak'}",
            ]
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else result.error or "Gagal.", result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    def _build_convert_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.convert_selector = FileSelector(multi=False, filter=_IMAGE_FILTER)
        v.addWidget(self.convert_selector)

        row = QHBoxLayout()
        row.addWidget(QLabel("Format tujuan:"))
        self.convert_format = QComboBox()
        for label, value in _CONVERT_FORMATS:
            self.convert_format.addItem(label, value)
        row.addWidget(self.convert_format)
        row.addSpacing(12)
        row.addWidget(QLabel("Kualitas JPEG/WebP:"))
        self.convert_quality = QSpinBox()
        self.convert_quality.setRange(1, 100)
        self.convert_quality.setValue(90)
        row.addWidget(self.convert_quality)
        row.addStretch()
        v.addLayout(row)

        self.convert_strip_meta = QCheckBox("Hapus metadata (EXIF)")
        v.addWidget(self.convert_strip_meta)

        v.addWidget(QLabel("Folder tujuan:"))
        self.convert_out = FolderSelector()
        v.addWidget(self.convert_out)

        btn = QPushButton("Konversi Gambar")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def work() -> JobResult:
            files = self.convert_selector.files()
            out_dir = self.convert_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file gambar terlebih dahulu.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            fmt = self.convert_format.currentData()
            try:
                res = processor.convert_image(
                    files[0],
                    out_dir,
                    fmt,
                    quality=self.convert_quality.value(),
                    remove_metadata=self.convert_strip_meta.isChecked(),
                )
            except (ValidationError, ProcessingError) as e:
                return JobResult(success=False, error=str(e))
            text = (
                f"Format tujuan   : {res.output.suffix.lstrip('.').upper()}\n"
                f"Ukuran sumber   : {res.input_size} byte\n"
                f"Ukuran hasil    : {res.output_size} byte\n"
                f"{_savings_text(res.savings_pct)}\n"
                f"Disimpan di     : {res.output}"
            )
            return JobResult(success=True, data={"text": text})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else result.error or "Gagal.", result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    def _build_resize_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.resize_selector = FileSelector(multi=False, filter=_IMAGE_FILTER)
        v.addWidget(self.resize_selector)

        self.resize_aspect_radio = QRadioButton("Lebar (jaga rasio aspek)")
        self.resize_percent_radio = QRadioButton("Persentase dari ukuran asli")
        self.resize_aspect_radio.setChecked(True)
        group = QButtonGroup(w)
        group.addButton(self.resize_aspect_radio)
        group.addButton(self.resize_percent_radio)
        v.addWidget(self.resize_aspect_radio)
        v.addWidget(self.resize_percent_radio)

        width_row = QHBoxLayout()
        width_row.addWidget(QLabel("Lebar (px):"))
        self.resize_width = QSpinBox()
        self.resize_width.setRange(1, 100000)
        self.resize_width.setValue(800)
        width_row.addWidget(self.resize_width)
        width_row.addStretch()
        v.addLayout(width_row)

        pct_row = QHBoxLayout()
        pct_row.addWidget(QLabel("Persentase (%):"))
        self.resize_pct = QSpinBox()
        self.resize_pct.setRange(1, 1000)
        self.resize_pct.setValue(50)
        self.resize_pct.setEnabled(False)
        pct_row.addWidget(self.resize_pct)
        pct_row.addStretch()
        v.addLayout(pct_row)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Format keluaran:"))
        self.resize_format = QComboBox()
        for label, value in _RESIZE_FORMATS:
            self.resize_format.addItem(label, value)
        fmt_row.addWidget(self.resize_format)
        fmt_row.addStretch()
        v.addLayout(fmt_row)

        self.resize_aspect_radio.toggled.connect(
            lambda on: (
                self.resize_width.setEnabled(on),
                self.resize_pct.setEnabled(not on),
            )
        )

        v.addWidget(QLabel("Folder tujuan:"))
        self.resize_out = FolderSelector()
        v.addWidget(self.resize_out)

        btn = QPushButton("Ubah Ukuran")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def work() -> JobResult:
            files = self.resize_selector.files()
            out_dir = self.resize_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file gambar terlebih dahulu.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            kwargs: Dict[str, object] = {"target_format": self.resize_format.currentData()}
            if self.resize_aspect_radio.isChecked():
                kwargs["width_px"] = self.resize_width.value()
                kwargs["keep_aspect"] = True
            else:
                kwargs["scale_pct"] = float(self.resize_pct.value())
            try:
                res = processor.resize_image(files[0], out_dir, **kwargs)
            except (ValidationError, ProcessingError) as e:
                return JobResult(success=False, error=str(e))
            text = (
                f"Ukuran asli     : {res.old_w} x {res.old_h} px\n"
                f"Ukuran baru     : {res.new_w} x {res.new_h} px\n"
                f"Ukuran sumber   : {res.input_size} byte\n"
                f"Ukuran hasil    : {res.output_size} byte\n"
                f"{_savings_text(res.savings_pct)}\n"
                f"Disimpan di     : {res.output}"
            )
            return JobResult(success=True, data={"text": text})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else result.error or "Gagal.", result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w
