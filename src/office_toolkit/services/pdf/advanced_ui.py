"""PDF Toolkit Lanjutan UI page: Phase 4 features (A8-A14 and advanced ops).

Covered tabs: Kompresi, PDF -> Gambar, Gambar -> PDF, Tambah Teks, Tambah Gambar,
Anotasi, Tanda Tangan, Proteksi, and Buka Proteksi. All heavy work runs on the Qt
worker via ``JobManager``; the worker closure only uses values captured on the UI
thread before the job starts, so widgets are never accessed from the worker.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from office_toolkit.core.job_manager import JobManager, JobResult
from office_toolkit.services.pdf import compress as compress_mod
from office_toolkit.services.pdf import edit as edit_mod
from office_toolkit.services.pdf import from_images as from_images_mod
from office_toolkit.services.pdf import render as render_mod
from office_toolkit.services.pdf import security as security_mod
from office_toolkit.ui.components.file_selector import FileSelector
from office_toolkit.ui.components.folder_selector import FolderSelector

_PDF_FILTER = "PDF (*.pdf)"
_IMAGE_FILTER = "Gambar (*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tif;*.tiff)"
_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")

_MODE_LABELS = {
    "struktur": "Struktur (lossless)",
    "images": "Optimasi gambar (lossy)",
    "rasterize": "Rasterisasi (agresif, lossy)",
}

_WARN_PER_MODE = {
    "struktur": "",
    "images": "Peringatan: mode ini mengoptimasi gambar dengan cara lossy "
    "(rekompresi); kualitas visual beberapa gambar dapat menurun.",
    "rasterize": "PERINGATAN: mode ini merasterisasi setiap halaman menjadi gambar. "
    "Teks yang dapat dicari, tautan, bookmark, formulir, dan anotasi TIDAK dipertahankan.",
}


def _hex_to_rgb(value: str) -> Tuple[float, float, float]:
    m = _HEX_RE.match((value or "").strip())
    if not m:
        raise ValueError("Format warna harus #RRGGBB (contoh: #FFC000).")
    hexv = m.group(1)
    return tuple(int(hexv[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def _result_view() -> QPlainTextEdit:
    view = QPlainTextEdit()
    view.setReadOnly(True)
    view.setPlaceholderText("Hasil akan ditampilkan di sini.")
    view.setMinimumHeight(70)
    return view


def _show(view: QPlainTextEdit, text: str, ok: bool) -> None:
    prefix = "" if ok else "[GAGAL] "
    view.setPlainText(prefix + text)


def _row() -> QHBoxLayout:
    r = QHBoxLayout()
    r.setContentsMargins(0, 0, 0, 0)
    return r


class PdfAdvancedPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pdfAdvancedPage")
        self.job_manager = JobManager()
        self.job_manager.job_finished.connect(self._on_job_finished)
        self._callbacks: Dict[str, Callable[[JobResult], None]] = {}

        layout = QVBoxLayout(self)
        title = QLabel("PDF Toolkit Lanjutan")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        desc = QLabel(
            "Kompresi, konversi halaman, gambar & teks, anotasi, tanda tangan, dan "
            "proteksi kata sandi (lokal/offline)."
        )
        layout.addWidget(desc)

        tabs = QTabWidget()
        tabs.addTab(self._build_compress_tab(), "Kompresi")
        tabs.addTab(self._build_to_images_tab(), "PDF → Gambar")
        tabs.addTab(self._build_images_to_pdf_tab(), "Gambar → PDF")
        tabs.addTab(self._build_add_text_tab(), "Tambah Teks")
        tabs.addTab(self._build_add_image_tab(), "Tambah Gambar")
        tabs.addTab(self._build_annotate_tab(), "Anotasi")
        tabs.addTab(self._build_signature_tab(), "Tanda Tangan")
        tabs.addTab(self._build_encrypt_tab(), "Proteksi")
        tabs.addTab(self._build_decrypt_tab(), "Buka Proteksi")
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

    def _require(self, view: QPlainTextEdit) -> None:
        _show(view, "", False)

    # -- Kompresi ---------------------------------------------------------
    def _build_compress_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("PDF sumber:"))
        self.compress_selector = FileSelector(multi=False, filter=_PDF_FILTER)
        v.addWidget(self.compress_selector)

        mode_row = _row()
        mode_row.addWidget(QLabel("Metode:"))
        self.compress_mode = QComboBox()
        for key in compress_mod.SUPPORTED_MODES:
            self.compress_mode.addItem(_MODE_LABELS[key], key)
        mode_row.addWidget(self.compress_mode, 1)
        v.addLayout(mode_row)

        self.compress_warn = QLabel("")
        self.compress_warn.setWordWrap(True)
        self.compress_warn.setStyleSheet("color: #b05e00;")
        v.addWidget(self.compress_warn)

        q_row = _row()
        q_row.addWidget(QLabel("Kualitas (lossy):"))
        self.compress_quality = QSpinBox()
        self.compress_quality.setRange(1, 100)
        self.compress_quality.setValue(80)
        q_row.addWidget(self.compress_quality)
        q_row.addSpacing(16)
        q_row.addWidget(QLabel("Target DPI gambar:"))
        self.compress_img_dpi = QSpinBox()
        self.compress_img_dpi.setRange(0, 600)
        self.compress_img_dpi.setValue(0)
        self.compress_img_dpi.setToolTip("0 = pertahankan resolusi asli")
        q_row.addWidget(self.compress_img_dpi)
        q_row.addSpacing(16)
        q_row.addWidget(QLabel("DPI rasterisasi:"))
        self.compress_raster_dpi = QSpinBox()
        self.compress_raster_dpi.setRange(36, 600)
        self.compress_raster_dpi.setValue(150)
        q_row.addWidget(self.compress_raster_dpi)
        q_row.addStretch()
        v.addLayout(q_row)

        v.addWidget(QLabel("Folder tujuan:"))
        self.compress_out = FolderSelector()
        v.addWidget(self.compress_out)
        v.addWidget(QLabel("Nama file hasil (opsional):"))
        self.compress_name = QLineEdit()
        v.addWidget(self.compress_name)
        btn = QPushButton("Kompres PDF")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def on_mode(index: int) -> None:
            key = self.compress_mode.itemData(index)
            self.compress_warn.setText(_WARN_PER_MODE.get(key or "", ""))
            is_images = key == compress_mod.MODE_IMAGES
            self.compress_quality.setEnabled(is_images)
            self.compress_img_dpi.setEnabled(is_images)
            self.compress_raster_dpi.setEnabled(key == compress_mod.MODE_RASTERIZE)

        self.compress_mode.currentIndexChanged.connect(on_mode)
        on_mode(0)

        def work() -> JobResult:
            files = [Path(f) for f in self.compress_selector.files()]
            out_dir = self.compress_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file PDF.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            kwargs = dict(
                mode=self.compress_mode.itemData(self.compress_mode.currentIndex()),
                quality=self.compress_quality.value(),
                image_dpi_target=self.compress_img_dpi.value(),
                rasterize_dpi=self.compress_raster_dpi.value(),
                output_name=self.compress_name.text().strip() or None,
            )
            res = compress_mod.compress_pdf(files[0], out_dir, **kwargs)
            lines = [
                f"Mode           : {_MODE_LABELS[res.mode]}",
                f"Ukuran awal    : {res.input_size} byte",
                f"Ukuran hasil   : {res.output_size} byte",
                f"Perubahan      : {res.savings_pct:+.2f}%",
                f"Jumlah halaman : {res.page_count}",
                f"Disimpan di    : {res.output}",
            ]
            if res.savings_pct < 0:
                lines.append("Catatan: hasil lebih BESAR dari sumber; kompresi tidak selalu memperkecil.")
            if res.warnings:
                lines.append("Peringatan:")
                lines.extend(f"  - {x}" for x in res.warnings)
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    # -- PDF -> Gambar ----------------------------------------------------
    def _build_to_images_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("PDF sumber:"))
        self.ti_selector = FileSelector(multi=False, filter=_PDF_FILTER)
        v.addWidget(self.ti_selector)

        row = _row()
        row.addWidget(QLabel("Format:"))
        self.ti_format = QComboBox()
        self.ti_format.addItems(["PNG", "JPEG"])
        row.addWidget(self.ti_format)
        row.addSpacing(16)
        row.addWidget(QLabel("DPI (36-600):"))
        self.ti_dpi = QSpinBox()
        self.ti_dpi.setRange(36, 600)
        self.ti_dpi.setValue(150)
        row.addWidget(self.ti_dpi)
        row.addSpacing(16)
        row.addWidget(QLabel("Halaman (kosong = semua):"))
        self.ti_pages = QLineEdit()
        self.ti_pages.setPlaceholderText("contoh: 1-3, 5")
        row.addWidget(self.ti_pages, 1)
        v.addLayout(row)

        v.addWidget(QLabel("Folder tujuan:"))
        self.ti_out = FolderSelector()
        v.addWidget(self.ti_out)
        v.addWidget(QLabel("Nama dasar file (opsional):"))
        self.ti_base = QLineEdit()
        v.addWidget(self.ti_base)
        btn = QPushButton("Render ke Gambar")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def work() -> JobResult:
            files = [Path(f) for f in self.ti_selector.files()]
            out_dir = self.ti_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file PDF.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            fmt = "png" if self.ti_format.currentText() == "PNG" else "jpg"
            pages = self.ti_pages.text().strip() or None
            res = render_mod.render_pdf_to_images(
                files[0], out_dir, fmt=fmt, dpi=self.ti_dpi.value(),
                pages=pages, base_name=self.ti_base.text().strip() or None,
            )
            lines = [
                f"Berhasil merender {res.rendered_count} dari {res.page_count} halaman.",
                f"Format: {res.format.upper()} | DPI: {res.dpi}",
                "File hasil:",
            ]
            lines.extend(f"  - {f.output.name}" for f in res.outputs)
            if res.failed:
                lines.append(f"Halaman gagal: {res.failed}")
            if res.warnings:
                lines.append("Catatan:")
                lines.extend(f"  - {x}" for x in res.warnings)
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    # -- Gambar -> PDF ----------------------------------------------------
    def _build_images_to_pdf_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.ip_selector = FileSelector(multi=True, filter=_IMAGE_FILTER)
        v.addWidget(self.ip_selector)

        v.addWidget(QLabel("Urutan gambar (gunakan tombol):"))
        row = QHBoxLayout()
        self.ip_list = QListWidget()
        row.addWidget(self.ip_list, 1)
        col = QVBoxLayout()
        up = QPushButton("Naik")
        down = QPushButton("Turun")
        remove = QPushButton("Hapus")
        col.addWidget(up)
        col.addWidget(down)
        col.addWidget(remove)
        col.addStretch()
        row.addLayout(col)
        v.addLayout(row, 1)

        p_row = _row()
        p_row.addWidget(QLabel("Ukuran halaman:"))
        self.ip_size = QComboBox()
        self.ip_size.addItems(["Ukuran gambar", "A4", "Letter"])
        p_row.addWidget(self.ip_size)
        p_row.addSpacing(12)
        p_row.addWidget(QLabel("Orientasi:"))
        self.ip_orient = QComboBox()
        self.ip_orient.addItems(["Auto", "Portrait", "Landscape"])
        p_row.addWidget(self.ip_orient)
        p_row.addSpacing(12)
        p_row.addWidget(QLabel("Penempatan:"))
        self.ip_fit = QComboBox()
        self.ip_fit.addItems(["Sesuaikan halaman", "Ukuran asli"])
        p_row.addWidget(self.ip_fit)
        p_row.addSpacing(12)
        p_row.addWidget(QLabel("Margin (pt):"))
        self.ip_margin = QDoubleSpinBox()
        self.ip_margin.setRange(0.0, 400.0)
        self.ip_margin.setValue(0.0)
        p_row.addWidget(self.ip_margin)
        p_row.addSpacing(12)
        p_row.addWidget(QLabel("Latar:"))
        self.ip_bg = QComboBox()
        self.ip_bg.addItems(["putih", "hitam", "transparan"])
        p_row.addWidget(self.ip_bg)
        p_row.addStretch()
        v.addLayout(p_row)

        v.addWidget(QLabel("Folder tujuan:"))
        self.ip_out = FolderSelector()
        v.addWidget(self.ip_out)
        v.addWidget(QLabel("Nama file hasil (opsional):"))
        self.ip_name = QLineEdit()
        v.addWidget(self.ip_name)
        btn = QPushButton("Buat PDF dari Gambar")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        self.ip_selector.files_changed.connect(self._populate_ip_list)

        def move(delta: int) -> None:
            i = self.ip_list.currentRow()
            j = i + delta
            if i < 0 or j < 0 or j >= self.ip_list.count():
                return
            item = self.ip_list.takeItem(i)
            self.ip_list.insertItem(j, item)
            self.ip_list.setCurrentRow(j)

        def remove_selected() -> None:
            i = self.ip_list.currentRow()
            if i >= 0:
                self.ip_list.takeItem(i)

        up.clicked.connect(lambda: move(-1))
        down.clicked.connect(lambda: move(1))
        remove.clicked.connect(remove_selected)

        def work() -> JobResult:
            files = [
                Path(self.ip_list.item(i).data(Qt.UserRole))
                for i in range(self.ip_list.count())
            ]
            out_dir = self.ip_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih minimal satu gambar.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            size_map = {"Ukuran gambar": "image", "A4": "a4", "Letter": "letter"}
            orient_map = {"Auto": "auto", "Portrait": "portrait", "Landscape": "landscape"}
            fit_map = {"Sesuaikan halaman": "fit", "Ukuran asli": "original"}
            bg_map = {"putih": "white", "hitam": "black", "transparan": "transparent"}
            res = from_images_mod.images_to_pdf(
                files,
                out_dir,
                page_size=size_map[self.ip_size.currentText()],
                orientation=orient_map[self.ip_orient.currentText()],
                fit_mode=fit_map[self.ip_fit.currentText()],
                margin_pt=self.ip_margin.value(),
                background=bg_map[self.ip_bg.currentText()],
                output_name=self.ip_name.text().strip() or None,
            )
            lines = [
                f"Berhasil membuat PDF {res.page_count} halaman dari {len(res.succeeded)} gambar.",
                f"Disimpan di: {res.output}",
            ]
            if res.failed:
                lines.append(f"Gagal: {len(res.failed)} gambar -> " + "; ".join(f"{n} ({e})" for n, e in res.failed))
            if res.warnings:
                lines.append("Catatan:")
                lines.extend(f"  - {x}" for x in res.warnings)
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    def _populate_ip_list(self, files: List[Path]) -> None:
        self.ip_list.clear()
        for f in files:
            self.ip_list.addItem(str(f))
            self.ip_list.item(self.ip_list.count() - 1).setData(Qt.UserRole, str(f))

    # -- Tambah Teks ------------------------------------------------------
    def _build_add_text_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("PDF sumber:"))
        self.at_selector = FileSelector(multi=False, filter=_PDF_FILTER)
        v.addWidget(self.at_selector)
        v.addWidget(QLabel("Teks yang ditambahkan:"))
        self.at_text = QPlainTextEdit()
        self.at_text.setPlaceholderText("Tulis teks di sini...")
        self.at_text.setMaximumHeight(90)
        v.addWidget(self.at_text)
        v.addWidget(QLabel("Halaman (contoh: 1, 2-4):"))
        self.at_pages = QLineEdit()
        v.addWidget(self.at_pages)

        p_row = _row()
        p_row.addWidget(QLabel("X:"))
        self.at_x = QDoubleSpinBox()
        self.at_x.setRange(0.0, 10000.0)
        self.at_x.setValue(50.0)
        p_row.addWidget(self.at_x)
        p_row.addSpacing(8)
        p_row.addWidget(QLabel("Y:"))
        self.at_y = QDoubleSpinBox()
        self.at_y.setRange(0.0, 10000.0)
        self.at_y.setValue(50.0)
        p_row.addWidget(self.at_y)
        p_row.addSpacing(8)
        p_row.addWidget(QLabel("Lebar kotak:"))
        self.at_width = QDoubleSpinBox()
        self.at_width.setRange(1.0, 10000.0)
        self.at_width.setValue(300.0)
        p_row.addWidget(self.at_width)
        p_row.addSpacing(8)
        p_row.addWidget(QLabel("Ukuran (pt):"))
        self.at_fontsize = QDoubleSpinBox()
        self.at_fontsize.setRange(1.0, 500.0)
        self.at_fontsize.setValue(12.0)
        p_row.addWidget(self.at_fontsize)
        p_row.addSpacing(8)
        p_row.addWidget(QLabel("Perataan:"))
        self.at_align = QComboBox()
        self.at_align.addItems(["Kiri", "Tengah", "Kanan", "Rata"])
        p_row.addWidget(self.at_align)
        p_row.addSpacing(8)
        p_row.addWidget(QLabel("Warna:"))
        self.at_color = QLineEdit("#000000")
        self.at_color.setMaximumWidth(90)
        p_row.addWidget(self.at_color)
        p_row.addStretch()
        v.addLayout(p_row)

        v.addWidget(QLabel("Folder tujuan:"))
        self.at_out = FolderSelector()
        v.addWidget(self.at_out)
        btn = QPushButton("Tambahkan Teks")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def work() -> JobResult:
            files = [Path(f) for f in self.at_selector.files()]
            out_dir = self.at_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file PDF.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            try:
                color = _hex_to_rgb(self.at_color.text())
            except ValueError as e:
                return JobResult(success=False, error=str(e))
            align_map = {"Kiri": "left", "Tengah": "center", "Kanan": "right", "Rata": "justify"}
            res = edit_mod.add_text_to_pdf(
                files[0], self.at_text.toPlainText(), self.at_pages.text(),
                out_dir, x=self.at_x.value(), y=self.at_y.value(),
                box_width=self.at_width.value(), fontsize=self.at_fontsize.value(),
                color=color, align=align_map[self.at_align.currentText()],
            )
            lines = [
                f"Berhasil menambahkan teks ke {len(res.inserted_pages)} halaman.",
                f"Disimpan di: {res.output}",
            ]
            if res.warnings:
                lines.append("Catatan:")
                lines.extend(f"  - {x}" for x in res.warnings)
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    # -- Tambah Gambar ----------------------------------------------------
    def _build_add_image_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("PDF sumber:"))
        self.ai_selector = FileSelector(multi=False, filter=_PDF_FILTER)
        v.addWidget(self.ai_selector)
        v.addWidget(QLabel("Gambar (logo/stempel):"))
        self.ai_image = FileSelector(multi=False, filter=_IMAGE_FILTER)
        v.addWidget(self.ai_image)
        v.addWidget(QLabel("Halaman (contoh: 1, 2-4):"))
        self.ai_pages = QLineEdit()
        v.addWidget(self.ai_pages)

        p_row = _row()
        p_row.addWidget(QLabel("X:"))
        self.ai_x = QDoubleSpinBox()
        self.ai_x.setRange(0.0, 10000.0)
        p_row.addWidget(self.ai_x)
        p_row.addSpacing(8)
        p_row.addWidget(QLabel("Y:"))
        self.ai_y = QDoubleSpinBox()
        self.ai_y.setRange(0.0, 10000.0)
        p_row.addWidget(self.ai_y)
        p_row.addSpacing(8)
        p_row.addWidget(QLabel("Lebar (pt):"))
        self.ai_w = QDoubleSpinBox()
        self.ai_w.setRange(1.0, 20000.0)
        self.ai_w.setValue(100.0)
        p_row.addWidget(self.ai_w)
        p_row.addSpacing(8)
        p_row.addWidget(QLabel("Tinggi (pt, 0=auto):"))
        self.ai_h = QDoubleSpinBox()
        self.ai_h.setRange(0.0, 20000.0)
        self.ai_h.setValue(0.0)
        p_row.addWidget(self.ai_h)
        p_row.addStretch()
        v.addLayout(p_row)

        self.ai_keep = QCheckBox("Pertahankan rasio aspek")
        self.ai_keep.setChecked(True)
        v.addWidget(self.ai_keep)

        v.addWidget(QLabel("Folder tujuan:"))
        self.ai_out = FolderSelector()
        v.addWidget(self.ai_out)
        btn = QPushButton("Tambahkan Gambar")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def work() -> JobResult:
            files = [Path(f) for f in self.ai_selector.files()]
            imgs = [Path(f) for f in self.ai_image.files()]
            out_dir = self.ai_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file PDF.")
            if not imgs:
                return JobResult(success=False, error="Pilih gambar.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            h = self.ai_h.value() or None
            res = edit_mod.add_image_to_pdf(
                files[0], imgs[0], self.ai_pages.text(), out_dir,
                x=self.ai_x.value(), y=self.ai_y.value(),
                width_pt=self.ai_w.value(), height_pt=h,
                keep_proportion=self.ai_keep.isChecked(),
            )
            lines = [
                f"Berhasil menambahkan gambar ke {len(res.placed_pages)} halaman.",
                f"Posisi/ukuran: {res.rect[0]:.1f},{res.rect[1]:.1f} -> "
                f"{res.rect[2]:.1f}x{res.rect[3]:.1f} pt",
                f"Disimpan di: {res.output}",
            ]
            if res.warnings:
                lines.append("Catatan:")
                lines.extend(f"  - {x}" for x in res.warnings)
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    # -- Anotasi ----------------------------------------------------------
    def _build_annotate_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("PDF sumber:"))
        self.an_selector = FileSelector(multi=False, filter=_PDF_FILTER)
        v.addWidget(self.an_selector)
        v.addWidget(QLabel("Halaman (contoh: 1, 2-4):"))
        self.an_pages = QLineEdit()
        v.addWidget(self.an_pages)

        type_row = _row()
        type_row.addWidget(QLabel("Jenis anotasi:"))
        self.an_type = QComboBox()
        self.an_type.addItems(["Highlight teks", "Catatan", "Kotak penanda", "Garis / panah"])
        type_row.addWidget(self.an_type)
        type_row.addStretch()
        v.addLayout(type_row)

        self.an_highlight_text = QLineEdit()
        self.an_highlight_text.setPlaceholderText("Teks sasaran untuk highlight (harus ada di halaman)")
        v.addWidget(self.an_highlight_text)

        note_box = QWidget()
        nv = QVBoxLayout(note_box)
        nv.setContentsMargins(0, 0, 0, 0)
        n_row = _row()
        n_row.addWidget(QLabel("Posisi catatan: X:"))
        self.an_nx = QDoubleSpinBox()
        self.an_nx.setRange(0.0, 10000.0)
        n_row.addWidget(self.an_nx)
        n_row.addSpacing(8)
        n_row.addWidget(QLabel("Y:"))
        self.an_ny = QDoubleSpinBox()
        self.an_ny.setRange(0.0, 10000.0)
        self.an_ny.setValue(100.0)
        n_row.addWidget(self.an_ny)
        n_row.addStretch()
        nv.addLayout(n_row)
        self.an_note_text = QPlainTextEdit()
        self.an_note_text.setPlaceholderText("Isi catatan (tidak tampil langsung di halaman)...")
        self.an_note_text.setMaximumHeight(70)
        nv.addWidget(self.an_note_text)
        v.addWidget(note_box)

        geom_box = QWidget()
        gv = QVBoxLayout(geom_box)
        gv.setContentsMargins(0, 0, 0, 0)
        r = _row()
        r.addWidget(QLabel("X1:"))
        self.an_x1 = QDoubleSpinBox()
        self.an_x1.setRange(0.0, 20000.0)
        r.addWidget(self.an_x1)
        r.addSpacing(8)
        r.addWidget(QLabel("Y1:"))
        self.an_y1 = QDoubleSpinBox()
        self.an_y1.setRange(0.0, 20000.0)
        r.addWidget(self.an_y1)
        r.addSpacing(8)
        r.addWidget(QLabel("X2:"))
        self.an_x2 = QDoubleSpinBox()
        self.an_x2.setRange(0.0, 20000.0)
        self.an_x2.setValue(100.0)
        r.addWidget(self.an_x2)
        r.addSpacing(8)
        r.addWidget(QLabel("Y2:"))
        self.an_y2 = QDoubleSpinBox()
        self.an_y2.setRange(0.0, 20000.0)
        self.an_y2.setValue(100.0)
        r.addWidget(self.an_y2)
        gv.addLayout(r)
        box_arrow_row = _row()
        self.an_arrow = QCheckBox("Ujung panah (untuk garis)")
        box_arrow_row.addWidget(self.an_arrow)
        box_arrow_row.addStretch()
        gv.addLayout(box_arrow_row)
        v.addWidget(geom_box)

        opt_row = _row()
        opt_row.addWidget(QLabel("Warna:"))
        self.an_color = QLineEdit("#FFCC00")
        self.an_color.setMaximumWidth(90)
        opt_row.addWidget(self.an_color)
        opt_row.addSpacing(8)
        opt_row.addWidget(QLabel("Opacity (0-1):"))
        self.an_opacity = QDoubleSpinBox()
        self.an_opacity.setRange(0.0, 1.0)
        self.an_opacity.setValue(0.8)
        self.an_opacity.setSingleStep(0.05)
        opt_row.addWidget(self.an_opacity)
        opt_row.addStretch()
        v.addLayout(opt_row)

        self.an_note_label = QLabel("Catatan: isi catatan tidak tampil sebagai teks di halaman; "
                                    "muncul saat ikon catatan dibuka oleh viewer.")
        self.an_note_label.setWordWrap(True)
        v.addWidget(self.an_note_label)

        v.addWidget(QLabel("Folder tujuan:"))
        self.an_out = FolderSelector()
        v.addWidget(self.an_out)
        btn = QPushButton("Tambahkan Anotasi")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def on_type(index: int) -> None:
            kind = self.an_type.currentText()
            self.an_highlight_text.setVisible(kind == "Highlight teks")
            note_box.setVisible(kind == "Catatan")
            geom_box.setVisible(kind in ("Kotak penanda", "Garis / panah"))
            self.an_note_label.setVisible(kind == "Catatan")

        self.an_type.currentIndexChanged.connect(on_type)
        on_type(0)

        def work() -> JobResult:
            files = [Path(f) for f in self.an_selector.files()]
            out_dir = self.an_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file PDF.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            try:
                color = _hex_to_rgb(self.an_color.text())
            except ValueError as e:
                return JobResult(success=False, error=str(e))
            kind = self.an_type.currentText()
            if kind == "Highlight teks":
                kargs = dict(annot_type="highlight", highlight_text=self.an_highlight_text.text())
            elif kind == "Catatan":
                kargs = dict(
                    annot_type="note",
                    note_pos=(self.an_nx.value(), self.an_ny.value()),
                    note_text=self.an_note_text.toPlainText(),
                )
            elif kind == "Kotak penanda":
                kargs = dict(annot_type="rect", rect=(self.an_x1.value(), self.an_y1.value(), self.an_x2.value(), self.an_y2.value()))
            else:
                kargs = dict(
                    annot_type="line",
                    line_p1=(self.an_x1.value(), self.an_y1.value()),
                    line_p2=(self.an_x2.value(), self.an_y2.value()),
                    arrow=self.an_arrow.isChecked(),
                )
            res = edit_mod.annotate_pdf(
                files[0], self.an_pages.text(), out_dir,
                color=color, opacity=self.an_opacity.value(), **kargs,
            )
            lines = [
                f"Berhasil menambahkan {res.annots_added} anotasi.",
                f"Disimpan di: {res.output}",
            ]
            if res.not_found:
                lines.append("Tidak dibuat (teks tidak ditemukan):")
                lines.extend(f"  - {x}" for x in res.not_found)
            if res.warnings:
                lines.append("Catatan:")
                lines.extend(f"  - {x}" for x in res.warnings)
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    # -- Tanda Tangan -----------------------------------------------------
    def _build_signature_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("PDF tujuan:"))
        self.sig_selector = FileSelector(multi=False, filter=_PDF_FILTER)
        v.addWidget(self.sig_selector)
        v.addWidget(QLabel("Gambar tanda tangan (PNG dengan latar transparan lebih baik):"))
        self.sig_image = FileSelector(multi=False, filter=_IMAGE_FILTER)
        v.addWidget(self.sig_image)
        self.sig_preview = QLabel("Belum ada gambar.")
        self.sig_preview.setMinimumHeight(40)
        self.sig_preview.setAlignment(Qt.AlignCenter)
        v.addWidget(self.sig_preview)
        self.sig_image.files_changed.connect(self._update_sig_preview)

        row = _row()
        row.addWidget(QLabel("Halaman:"))
        self.sig_page = QSpinBox()
        self.sig_page.setRange(1, 9999)
        self.sig_page.setValue(1)
        row.addWidget(self.sig_page)
        row.addSpacing(16)
        row.addWidget(QLabel("X:"))
        self.sig_x = QDoubleSpinBox()
        self.sig_x.setRange(0.0, 10000.0)
        row.addWidget(self.sig_x)
        row.addSpacing(8)
        row.addWidget(QLabel("Y:"))
        self.sig_y = QDoubleSpinBox()
        self.sig_y.setRange(0.0, 10000.0)
        row.addWidget(self.sig_y)
        row.addSpacing(8)
        row.addWidget(QLabel("Lebar (pt):"))
        self.sig_w = QDoubleSpinBox()
        self.sig_w.setRange(1.0, 20000.0)
        self.sig_w.setValue(120.0)
        row.addWidget(self.sig_w)
        row.addStretch()
        v.addLayout(row)

        note = QLabel("Catatan penting: gambar tanda tangan BUKAN tanda tangan digital "
                      "bersertifikat. Tidak menjamin identitas penandatangan, integritas "
                      "kriptografis, atau keaslian dokumen.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #b05e00;")
        v.addWidget(note)

        v.addWidget(QLabel("Folder tujuan:"))
        self.sig_out = FolderSelector()
        v.addWidget(self.sig_out)
        btn = QPushButton("Simpan PDF Tanda Tangan")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def work() -> JobResult:
            files = [Path(f) for f in self.sig_selector.files()]
            imgs = [Path(f) for f in self.sig_image.files()]
            out_dir = self.sig_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file PDF.")
            if not imgs:
                return JobResult(success=False, error="Pilih gambar tanda tangan.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            res = edit_mod.add_signature_image(
                files[0], imgs[0], self.sig_page.value(), out_dir,
                x=self.sig_x.value(), y=self.sig_y.value(), width_pt=self.sig_w.value(),
            )
            lines = [
                f"Tanda tangan ditempatkan pada halaman {res.placed_page} "
                f"({res.rect[2]:.1f}x{res.rect[3]:.1f} pt).",
                f"Disimpan di: {res.output}",
            ]
            lines.extend(f"  - {x}" for x in res.warnings)
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def run_with_confirm() -> None:
            files = [Path(f) for f in self.sig_selector.files()]
            imgs = [Path(f) for f in self.sig_image.files()]
            if not files or not imgs:
                _show(view, "Pilih PDF tujuan dan gambar tanda tangan.", False)
                return
            ans = QMessageBox.warning(
                w,
                "Konfirmasi Tanda Tangan",
                "Anda akan menyisipkan GAMBAR tanda tangan.\n\n"
                "Ini BUKAN tanda tangan digital bersertifikat dan tidak menjamin "
                "identitas, keaslian, atau integritas dokumen. Gambar tanda tangan "
                "dapat disalin atau dipindahkan oleh pihak lain.\n\n"
                "Jika halaman/posisi sudah benar, klik OK untuk menyimpan.",
                QMessageBox.Ok | QMessageBox.Cancel,
            )
            if ans == QMessageBox.Ok:
                self._run(btn, work, done)

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(run_with_confirm)
        return w

    def _update_sig_preview(self, files: List[Path]) -> None:
        if not files:
            self.sig_preview.setText("Belum ada gambar.")
            self.sig_preview.setPixmap(QPixmap())
            return
        pix = QPixmap(str(files[0]))
        if pix.isNull():
            self.sig_preview.setText("Tidak dapat membaca gambar.")
            return
        self.sig_preview.setPixmap(pix.scaledToHeight(120))

    # -- Proteksi ---------------------------------------------------------
    def _build_encrypt_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("PDF sumber:"))
        self.enc_selector = FileSelector(multi=False, filter=_PDF_FILTER)
        v.addWidget(self.enc_selector)

        pw_row = _row()
        pw_row.addWidget(QLabel("Kata sandi pengguna (min 4):"))
        self.enc_user = QLineEdit()
        self.enc_user.setEchoMode(QLineEdit.Password)
        pw_row.addWidget(self.enc_user)
        pw_row.addSpacing(8)
        pw_row.addWidget(QLabel("Ulangi:"))
        self.enc_user2 = QLineEdit()
        self.enc_user2.setEchoMode(QLineEdit.Password)
        pw_row.addWidget(self.enc_user2)
        v.addLayout(pw_row)

        ow_row = _row()
        ow_row.addWidget(QLabel("Kata sandi pemilik (min 4):"))
        self.enc_owner = QLineEdit()
        self.enc_owner.setEchoMode(QLineEdit.Password)
        ow_row.addWidget(self.enc_owner)
        ow_row.addSpacing(8)
        ow_row.addWidget(QLabel("Ulangi:"))
        self.enc_owner2 = QLineEdit()
        self.enc_owner2.setEchoMode(QLineEdit.Password)
        ow_row.addWidget(self.enc_owner2)
        v.addLayout(ow_row)

        alg_row = _row()
        alg_row.addWidget(QLabel("Algoritma:"))
        self.enc_alg = QComboBox()
        self.enc_alg.addItems(["AES-256", "AES-128"])
        alg_row.addWidget(self.enc_alg)
        alg_row.addStretch()
        v.addLayout(alg_row)

        v.addWidget(QLabel("Izin dokumen (himbauan, tidak dibatasi semua viewer):"))
        self.enc_allow_print = QCheckBox("Izinkan mencetak")
        self.enc_allow_print.setChecked(True)
        self.enc_allow_copy = QCheckBox("Izinkan menyalin")
        self.enc_allow_modify = QCheckBox("Izinkan memodifikasi/merakit")
        self.enc_allow_annotate = QCheckBox("Izinkan anotasi/formulir")
        for cb in (self.enc_allow_print, self.enc_allow_copy, self.enc_allow_modify, self.enc_allow_annotate):
            v.addWidget(cb)

        v.addWidget(QLabel("Folder tujuan:"))
        self.enc_out = FolderSelector()
        v.addWidget(self.enc_out)
        v.addWidget(QLabel("Nama file hasil (opsional):"))
        self.enc_name = QLineEdit()
        v.addWidget(self.enc_name)
        btn = QPushButton("Proteksi PDF")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def work() -> JobResult:
            files = [Path(f) for f in self.enc_selector.files()]
            out_dir = self.enc_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file PDF.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            user = self.enc_user.text()
            if user != self.enc_user2.text():
                return JobResult(success=False, error="Konfirmasi kata sandi pengguna tidak cocok.")
            owner = self.enc_owner.text()
            if owner != self.enc_owner2.text():
                return JobResult(success=False, error="Konfirmasi kata sandi pemilik tidak cocok.")
            res = security_mod.encrypt_pdf(
                files[0], user, owner, out_dir,
                algorithm=self.enc_alg.currentText(),
                allow_print=self.enc_allow_print.isChecked(),
                allow_copy=self.enc_allow_copy.isChecked(),
                allow_modify=self.enc_allow_modify.isChecked(),
                allow_annotate=self.enc_allow_annotate.isChecked(),
                output_name=self.enc_name.text().strip() or None,
            )
            lines = [
                f"Berhasil melindungi PDF ({res.algorithm}).",
                f"Jumlah halaman tetap: {res.page_count}",
                f"Ukuran hasil: {res.output_size} byte",
                f"Disimpan di: {res.output}",
            ]
            lines.extend(f"  - {x}" for x in res.warnings)
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    # -- Buka Proteksi ----------------------------------------------------
    def _build_decrypt_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("PDF terenkripsi:"))
        self.dec_selector = FileSelector(multi=False, filter=_PDF_FILTER)
        v.addWidget(self.dec_selector)

        pw_row = _row()
        pw_row.addWidget(QLabel("Kata sandi:"))
        self.dec_pw = QLineEdit()
        self.dec_pw.setEchoMode(QLineEdit.Password)
        pw_row.addWidget(self.dec_pw)
        pw_row.addStretch()
        v.addLayout(pw_row)

        warn = QLabel("Setelah dibuka, file hasil TIDAK lagi dilindungi enkripsi sumber "
                      "dan dapat dibuka siapa saja yang memegang filenya.")
        warn.setWordWrap(True)
        warn.setStyleSheet("color: #b05e00;")
        v.addWidget(warn)

        v.addWidget(QLabel("Folder tujuan:"))
        self.dec_out = FolderSelector()
        v.addWidget(self.dec_out)
        v.addWidget(QLabel("Nama file hasil (opsional):"))
        self.dec_name = QLineEdit()
        v.addWidget(self.dec_name)
        btn = QPushButton("Buka Proteksi")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def work() -> JobResult:
            files = [Path(f) for f in self.dec_selector.files()]
            out_dir = self.dec_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file PDF terenkripsi.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            res = security_mod.decrypt_pdf(
                files[0], self.dec_pw.text(), out_dir,
                output_name=self.dec_name.text().strip() or None,
            )
            lines = [
                f"Berhasil membuka proteksi ({res.page_count} halaman).",
                f"Status enkripsi hasil: {'terenkripsi' if res.is_encrypted else 'tidak terenkripsi'}",
                f"Disimpan di: {res.output}",
                "Peringatan: hasil tidak lagi dilindungi enkripsi sumber.",
            ]
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def run_with_confirm() -> None:
            files = [Path(f) for f in self.dec_selector.files()]
            if not files:
                _show(view, "Pilih PDF terenkripsi.", False)
                return
            if not self.dec_pw.text():
                _show(view, "Masukkan kata sandi terlebih dahulu.", False)
                return
            ans = QMessageBox.warning(
                w,
                "Konfirmasi Membuka Proteksi",
                "Anda membuka proteksi dengan kata sandi yang diketahui.\n\n"
                "File hasil TIDAK lagi terenkripsi dan dapat dibuka oleh siapa pun "
                "yang memegangnya. Operasi ini tidak boleh digunakan untuk membuka "
                "file tanpa otorisasi.\n\n"
                "Lanjutkan?",
                QMessageBox.Ok | QMessageBox.Cancel,
            )
            if ans == QMessageBox.Ok:
                self._run(btn, work, done)

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(run_with_confirm)
        return w