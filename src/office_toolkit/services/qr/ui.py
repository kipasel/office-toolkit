"""QR Toolkit UI page: generate, design, logo, export, CSV batch, and decode.

Phase 5, Modul C (C1-C6). All heavy work runs on the Qt worker via
``JobManager``; widget values are captured on the UI thread before the job
starts. The QR preview is a real QR generated from the current input (never a
demo), and the decoded payload is never logged or auto-opened.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from office_toolkit.core.job_manager import JobManager, JobResult
from office_toolkit.core.errors import ValidationError
from office_toolkit.services.qr import csv_batch as csv_mod
from office_toolkit.services.qr import decoder as decoder_mod
from office_toolkit.services.qr import generator as gen_mod
from office_toolkit.services.qr.generator import MAX_LOGO_FRACTION, QrDesign
from office_toolkit.ui.components.file_selector import FileSelector
from office_toolkit.ui.components.folder_selector import FolderSelector

_IMAGE_FILTER = "Gambar (*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.gif)"
_CSV_FILTER = "CSV (*.csv)"
_PREVIEW_MAX = 220


class _ProgressEmitter(QObject):
    report = Signal(int)


def _row() -> QHBoxLayout:
    r = QHBoxLayout()
    r.setContentsMargins(0, 0, 0, 0)
    return r


def _result_view() -> QPlainTextEdit:
    view = QPlainTextEdit()
    view.setReadOnly(True)
    view.setPlaceholderText("Hasil akan ditampilkan di sini.")
    view.setMinimumHeight(70)
    return view


def _show(view: QPlainTextEdit, text: str, ok: bool) -> None:
    view.setPlainText(("" if ok else "[GAGAL] ") + text)


def _pixmap_from_pil(img, max_size: int) -> QPixmap:
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    pix = QPixmap()
    pix.loadFromData(buf.getvalue())
    return pix.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class QrToolkitPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("qrPage")
        self.job_manager = JobManager()
        self.job_manager.job_finished.connect(self._on_job_finished)
        self._callbacks: Dict[str, Callable[[JobResult], None]] = {}
        self.csv_progress = _ProgressEmitter()
        self._gen_preview_timer = QTimer(self)
        self._gen_preview_timer.setSingleShot(True)
        self._gen_preview_timer.timeout.connect(self._refresh_gen_preview)

        layout = QVBoxLayout(self)
        title = QLabel("QR Toolkit")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        desc = QLabel(
            "Buat QR Code, buat massal dari CSV, dan baca QR dari gambar "
            "(lokal/offline, tanpa membuka tautan otomatis)."
        )
        layout.addWidget(desc)

        tabs = QTabWidget()
        tabs.addTab(self._build_generate_tab(), "Buat QR")
        tabs.addTab(self._build_batch_tab(), "Batch dari CSV")
        tabs.addTab(self._build_decode_tab(), "Baca QR")
        layout.addWidget(tabs, 1)

    # -- job plumbing ---------------------------------------------------
    def _run(self, button, func, on_done) -> None:
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

    # -- design capture -------------------------------------------------
    def _current_design(self, logo_path: Optional[Path] = None) -> QrDesign:
        return QrDesign(
            box_size=self.gen_box.value(),
            border=self.gen_border.value(),
            fg_color=self.gen_fg.text().strip() or "#000000",
            bg_color=self.gen_bg.text().strip() or "#FFFFFF",
            error_correction=self.gen_ecc.itemData(self.gen_ecc.currentIndex()),
            logo_path=logo_path,
            logo_fraction=self.gen_logo_fraction.value(),
        )

    def _batch_design(self) -> QrDesign:
        return QrDesign(
            box_size=self.csv_box.value(),
            border=self.csv_border.value(),
            fg_color=self.csv_fg.text().strip() or "#000000",
            bg_color=self.csv_bg.text().strip() or "#FFFFFF",
            error_correction=self.csv_ecc.itemData(self.csv_ecc.currentIndex()),
            logo_path=None,
        )

    # -- Buat QR ---------------------------------------------------------
    def _build_generate_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Isi data QR (teks, URL, nomor):"))
        self.gen_data = QPlainTextEdit()
        self.gen_data.setPlaceholderText("Contoh: https://contoh.id/berkas atau Nomor: 12345")
        self.gen_data.setMaximumHeight(90)
        v.addWidget(self.gen_data)

        v.addWidget(QLabel("Pratinjau (QR asli dari data di atas):"))
        self.gen_preview = QLabel()
        self.gen_preview.setFixedWidth(_PREVIEW_MAX + 140)
        self.gen_preview.setMinimumHeight(_PREVIEW_MAX)
        self.gen_preview.setAlignment(Qt.AlignCenter)
        self.gen_preview.setStyleSheet("border: 1px dashed #999;")
        self.gen_preview.setToolTip("Pratinjau: QR yang benar-benar dihasilkan dari data Anda.")
        v.addWidget(self.gen_preview)
        self.gen_warn = QLabel("")
        self.gen_warn.setWordWrap(True)
        self.gen_warn.setStyleSheet("color: #b05e00;")
        v.addWidget(self.gen_warn)

        d_row = _row()
        d_row.addWidget(QLabel("Ukuran modul:"))
        self.gen_box = QSpinBox()
        self.gen_box.setRange(1, 60)
        self.gen_box.setValue(8)
        d_row.addWidget(self.gen_box)
        d_row.addSpacing(12)
        d_row.addWidget(QLabel("Quiet zone:"))
        self.gen_border = QSpinBox()
        self.gen_border.setRange(0, 20)
        self.gen_border.setValue(4)
        self.gen_border.setToolTip("Ruang kosong di sekitar QR (modul). Disarankan 4.")
        d_row.addWidget(self.gen_border)
        d_row.addSpacing(12)
        d_row.addWidget(QLabel("Error correction:"))
        self.gen_ecc = QComboBox()
        for key, label in gen_mod.ECC_LABELS.items():
            self.gen_ecc.addItem(label, key)
        d_row.addWidget(self.gen_ecc, 1)
        v.addLayout(d_row)

        c_row = _row()
        c_row.addWidget(QLabel("Warna isi (#RRGGBB):"))
        self.gen_fg = QLineEdit("#000000")
        self.gen_fg.setMaximumWidth(100)
        c_row.addWidget(self.gen_fg)
        c_row.addSpacing(8)
        c_row.addWidget(QLabel("Warna latar (#RRGGBB):"))
        self.gen_bg = QLineEdit("#FFFFFF")
        self.gen_bg.setMaximumWidth(100)
        c_row.addWidget(self.gen_bg)
        c_row.addStretch()
        v.addLayout(c_row)

        l_row = _row()
        l_row.addWidget(QLabel("Logo tengah (opsional):"))
        self.gen_logo = FileSelector(multi=False, filter=_IMAGE_FILTER)
        l_row.addWidget(self.gen_logo, 1)
        l_row.addSpacing(8)
        l_row.addWidget(QLabel("Lebar logo:"))
        self.gen_logo_fraction = QDoubleSpinBox()
        self.gen_logo_fraction.setRange(0.05, MAX_LOGO_FRACTION)
        self.gen_logo_fraction.setSingleStep(0.05)
        self.gen_logo_fraction.setValue(gen_mod.DEFAULT_LOGO_FRACTION)
        self.gen_logo_fraction.setDecimals(2)
        self.gen_logo_fraction.setSuffix(" dari QR")
        l_row.addWidget(self.gen_logo_fraction)
        v.addLayout(l_row)

        v.addWidget(QLabel("Folder tujuan:"))
        self.gen_out = FolderSelector()
        v.addWidget(self.gen_out)
        v.addWidget(QLabel("Nama file (opsional):"))
        self.gen_name = QLineEdit()
        v.addWidget(self.gen_name)

        btn_row = _row()
        self.gen_png_btn = QPushButton("Simpan PNG")
        self.gen_svg_btn = QPushButton("Simpan SVG")
        btn_row.addWidget(self.gen_png_btn)
        btn_row.addWidget(self.gen_svg_btn)
        btn_row.addStretch()
        v.addLayout(btn_row)
        self.gen_progress = QProgressBar()
        self.gen_progress.setVisible(False)
        v.addWidget(self.gen_progress)
        self.gen_result = _result_view()
        v.addWidget(self.gen_result, 1)

        def on_data_changed() -> None:
            self._gen_preview_timer.start(250)

        self.gen_data.textChanged.connect(on_data_changed)
        self.gen_logo.files_changed.connect(lambda _f: self._refresh_gen_preview())

        def _schedule_preview() -> None:
            self._gen_preview_timer.start(60)

        self.gen_box.valueChanged.connect(_schedule_preview)
        self.gen_border.valueChanged.connect(_schedule_preview)
        self.gen_ecc.currentIndexChanged.connect(_schedule_preview)
        self.gen_fg.textChanged.connect(_schedule_preview)
        self.gen_bg.textChanged.connect(_schedule_preview)
        self.gen_logo_fraction.valueChanged.connect(_schedule_preview)
        self._refresh_gen_preview()

        def _export(fmt: str) -> JobResult:
            files_out = self.gen_out.folder()
            logo_files = self.gen_logo.files()
            if not self.gen_data.toPlainText().strip():
                return JobResult(success=False, error="Isi data QR terlebih dahulu.")
            if files_out is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            logo = None
            if logo_files:
                logo = logo_files[0]
            design = self._current_design(logo_path=logo)
            name = self.gen_name.text().strip() or None
            try:
                if fmt == "svg":
                    res = gen_mod.render_qr_svg(
                        self.gen_data.toPlainText(), files_out, design=design, output_name=name
                    )
                else:
                    res = gen_mod.render_qr_png(
                        self.gen_data.toPlainText(), files_out, design=design, output_name=name
                    )
            except ValidationError as e:
                return JobResult(success=False, error=str(e))
            except Exception as e:  # pragma: no cover - defensive
                return JobResult(success=False, error=f"Gagal menyimpan QR: {e}")
            lines = [
                f"QR tersimpan: {res.output}",
                f"Format   : {res.fmt}",
            ]
            lines.extend(f"Peringatan : {x}" for x in res.warnings)
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def _done(view) -> Callable[[JobResult], None]:
            def done(result: JobResult) -> None:
                _show(view, result.data.get("text", "") if result.success else result.error or "Gagal.", result.success)
            return done

        def run_png() -> None:
            self._run(self.gen_png_btn, lambda: _export("png"), _done(self.gen_result))

        def run_svg() -> None:
            self._run(self.gen_svg_btn, lambda: _export("svg"), _done(self.gen_result))

        self.gen_png_btn.clicked.connect(run_png)
        self.gen_svg_btn.clicked.connect(run_svg)
        return w

    def _refresh_gen_preview(self) -> None:
        from office_toolkit.services.qr import generator as _gen
        from PySide6.QtGui import QPixmap as _P

        data = self.gen_data.toPlainText()
        logo_files = self.gen_logo.files()
        logo = logo_files[0] if logo_files else None
        warn: List[str] = []
        try:
            img, warn = _gen.build_qr_image(data, self._current_design(logo_path=logo))
            self.gen_preview.setPixmap(_pixmap_from_pil(img, _PREVIEW_MAX))
        except ValidationError as e:
            self.gen_preview.setPixmap(_P())
            warn = [str(e)]
        except Exception as e:  # pragma: no cover - defensive
            self.gen_preview.setPixmap(_P())
            warn = [f"Tidak dapat membuat pratinjau: {e}"]
        self.gen_warn.setText("\n".join(warn))

    # -- Batch CSV -------------------------------------------------------
    def _build_batch_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("File CSV (UTF-8, dengan atau tanpa BOM):"))
        self.csv_selector = FileSelector(multi=False, filter=_CSV_FILTER)
        v.addWidget(self.csv_selector)

        c_row = _row()
        c_row.addWidget(QLabel("Kolom isi QR:"))
        self.csv_content = QComboBox()
        c_row.addWidget(self.csv_content, 1)
        c_row.addSpacing(12)
        c_row.addWidget(QLabel("Kolom nama file (opsional):"))
        self.csv_filename = QComboBox()
        self.csv_filename.addItem("— (nomor urut otomatis)", None)
        c_row.addWidget(self.csv_filename, 1)
        v.addLayout(c_row)

        self.csv_preview = QLabel("Pilih file CSV untuk melihat pratinjau kolom & baris.")
        self.csv_preview.setWordWrap(True)
        self.csv_preview.setStyleSheet("color: #555;")
        v.addWidget(self.csv_preview)

        d_row = _row()
        d_row.addWidget(QLabel("Format:"))
        self.csv_fmt = QComboBox()
        self.csv_fmt.addItems(["PNG", "SVG"])
        d_row.addWidget(self.csv_fmt)
        d_row.addSpacing(12)
        d_row.addWidget(QLabel("Ukuran modul:"))
        self.csv_box = QSpinBox()
        self.csv_box.setRange(1, 60)
        self.csv_box.setValue(8)
        d_row.addWidget(self.csv_box)
        d_row.addSpacing(12)
        d_row.addWidget(QLabel("Quiet zone:"))
        self.csv_border = QSpinBox()
        self.csv_border.setRange(0, 20)
        self.csv_border.setValue(4)
        d_row.addWidget(self.csv_border)
        d_row.addSpacing(12)
        d_row.addWidget(QLabel("Error correction:"))
        self.csv_ecc = QComboBox()
        for key, label in gen_mod.ECC_LABELS.items():
            self.csv_ecc.addItem(label, key)
        d_row.addWidget(self.csv_ecc, 1)
        v.addLayout(d_row)

        cc_row = _row()
        cc_row.addWidget(QLabel("Warna isi (#RRGGBB):"))
        self.csv_fg = QLineEdit("#000000")
        self.csv_fg.setMaximumWidth(100)
        cc_row.addWidget(self.csv_fg)
        cc_row.addSpacing(8)
        cc_row.addWidget(QLabel("Warna latar (#RRGGBB):"))
        self.csv_bg = QLineEdit("#FFFFFF")
        self.csv_bg.setMaximumWidth(100)
        cc_row.addWidget(self.csv_bg)
        cc_row.addStretch()
        v.addLayout(cc_row)

        v.addWidget(QLabel("Folder tujuan:"))
        self.csv_out = FolderSelector()
        v.addWidget(self.csv_out)
        btn = QPushButton("Buat QR Massal")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        self.csv_progressbar = QProgressBar()
        self.csv_progressbar.setRange(0, 100)
        self.csv_progressbar.setValue(0)
        v.addWidget(self.csv_progressbar)
        self.csv_result = _result_view()
        v.addWidget(self.csv_result, 1)

        self.csv_progress.report.connect(self.csv_progressbar.setValue)

        def on_csv_picked(files: List[Path]) -> None:
            self.csv_content.clear()
            self.csv_filename.clear()
            self.csv_filename.addItem("— (nomor urut otomatis)", None)
            if not files:
                self.csv_preview.setText("Pilih file CSV untuk melihat pratinjau kolom & baris.")
                return
            try:
                header, preview = csv_mod.preview_csv(files[0])
            except ValidationError as e:
                self.csv_preview.setText(f"Error: {e}")
                return
            for h in header:
                self.csv_content.addItem(h, h)
                self.csv_filename.addItem(h, h)
            if header:
                self.csv_content.setCurrentIndex(0)
            rows_txt = "; ".join(" | ".join(c for c in r[:6]) for r in preview[:5])
            self.csv_preview.setText(
                f"Kolom: {', '.join(header)}\nContoh baris: {rows_txt or '(tidak ada baris data)'}"
            )

        self.csv_selector.files_changed.connect(on_csv_picked)

        def work() -> JobResult:
            files = self.csv_selector.files()
            out_dir = self.csv_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih file CSV.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            content_col = self.csv_content.itemData(self.csv_content.currentIndex())
            if not content_col:
                return JobResult(success=False, error="Pilih kolom yang berisi data QR.")
            filename_col = self.csv_filename.itemData(self.csv_filename.currentIndex())
            fmt = "png" if self.csv_fmt.currentText() == "PNG" else "svg"
            total_ref = {"n": 0}
            progress_emitter = self.csv_progress

            def on_progress(current: int, total: int) -> None:
                total_ref["n"] = total
                pct = int(current * 100 / total) if total else 0
                progress_emitter.report.emit(pct)

            try:
                res = csv_mod.process_csv_batch(
                    files[0], out_dir, content_col,
                    filename_column=filename_col, fmt=fmt,
                    design=self._batch_design(), progress_cb=on_progress,
                )
            except ValidationError as e:
                return JobResult(success=False, error=str(e))
            except Exception as e:
                return JobResult(success=False, error=f"Gagal memproses batch: {e}")
            progress_emitter.report.emit(100 if res.succeeded else 0)
            lines = [
                f"Total baris data : {res.total_rows}",
                f"Berhasil dibuat  : {len(res.succeeded)}",
                f"Dilewati (kosong): {res.skipped_rows}",
                f"Gagal            : {len(res.failed)}",
                f"Folder tujuan    : {res.output_dir}",
            ]
            if res.succeeded:
                lines.append("File dibuat:")
                lines.extend(f"  - {p.name}" for p in res.succeeded[:20])
                if len(res.succeeded) > 20:
                    lines.append(f"  ... dan {len(res.succeeded) - 20} file lainnya.")
            if res.failed:
                lines.append("Error per baris:")
                lines.extend(f"  - Baris {line}: {msg}" for line, msg in res.failed[:20])
                if len(res.failed) > 20:
                    lines.append(f"  ... dan {len(res.failed) - 20} error lain.")
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def done(result: JobResult) -> None:
            _show(self.csv_result, result.data.get("text", "") if result.success else result.error or "Gagal.", result.success)
            self.csv_progressbar.setValue(0)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    # -- Baca QR ---------------------------------------------------------
    def _build_decode_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Gambar sumber (PNG/JPEG/WebP/BMP):"))
        self.dec_selector = FileSelector(multi=False, filter=_IMAGE_FILTER)
        v.addWidget(self.dec_selector)
        self.dec_preview = QLabel("Belum ada gambar.")
        self.dec_preview.setMinimumHeight(_PREVIEW_MAX)
        self.dec_preview.setAlignment(Qt.AlignCenter)
        self.dec_preview.setStyleSheet("border: 1px dashed #999;")
        v.addWidget(self.dec_preview)
        self.dec_selector.files_changed.connect(self._update_decode_preview)

        note = QLabel(
            "Catatan: isi QR hanya ditampilkan di layar; file tidak dikirim ke mana pun, "
            "dan tautan di dalam QR tidak akan dibuka otomatis."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #555;")
        v.addWidget(note)

        btn = QPushButton("Baca QR")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        self.dec_result = _result_view()
        v.addWidget(self.dec_result, 1)

        def work() -> JobResult:
            files = self.dec_selector.files()
            if not files:
                return JobResult(success=False, error="Pilih gambar terlebih dahulu.")
            try:
                res = decoder_mod.decode_qr(files[0])
            except ValidationError as e:
                return JobResult(success=False, error=str(e))
            except Exception as e:
                return JobResult(success=False, error=f"Gagal membaca QR: {e}")
            if not res.found:
                lines = ["QR Code tidak ditemukan pada gambar."]
                lines.extend(f"Catatan: {x}" for x in res.warnings)
                return JobResult(success=True, data={"text": "\n".join(lines)})
            lines = [f"Ditemukan {len(res.items)} QR Code:"]
            for i, item in enumerate(res.items, start=1):
                lines.append(f"{i}. {item.text}")
            lines.extend(f"Catatan: {x}" for x in res.warnings)
            lines.append("Peringatan: jangan tempel/membuka isi QR dari sumber yang tidak dikenal secara otomatis.")
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def done(result: JobResult) -> None:
            _show(self.dec_result, result.data.get("text", "") if result.success else result.error or "Gagal.", result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    def _update_decode_preview(self, files: List[Path]) -> None:
        if not files:
            self.dec_preview.setText("Belum ada gambar.")
            self.dec_preview.setPixmap(QPixmap())
            return
        pix = QPixmap(str(files[0]))
        if pix.isNull():
            self.dec_preview.setText("Tidak dapat membaca gambar.")
            return
        self.dec_preview.setPixmap(pix.scaled(_PREVIEW_MAX, _PREVIEW_MAX, Qt.KeepAspectRatio, Qt.SmoothTransformation))