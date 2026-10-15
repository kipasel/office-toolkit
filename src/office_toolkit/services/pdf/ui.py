"""PDF Toolkit UI page: info, merge, split, extract, reorder, and rotate.

The page follows the existing Phase 1 conventions: Indonesian labels, the shared
``FileSelector``/``FolderSelector`` components, and heavy work executed on the Qt
worker via ``JobManager`` (the UI thread never performs file processing directly).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from office_toolkit.core.job_manager import JobManager, JobResult
from office_toolkit.services.pdf import processor
from office_toolkit.ui.components.file_selector import FileSelector
from office_toolkit.ui.components.folder_selector import FolderSelector

_PDF_FILTER = "PDF (*.pdf)"


def _result_view() -> QPlainTextEdit:
    view = QPlainTextEdit()
    view.setReadOnly(True)
    view.setPlaceholderText("Hasil akan ditampilkan di sini.")
    view.setMinimumHeight(70)
    return view


def _show(view: QPlainTextEdit, text: str, ok: bool) -> None:
    prefix = "" if ok else "[GAGAL] "
    view.setPlainText(prefix + text)


class PdfToolkitPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pdfToolkitPage")
        self.job_manager = JobManager()
        self.job_manager.job_finished.connect(self._on_job_finished)
        self._callbacks: Dict[str, Callable[[JobResult], None]] = {}

        layout = QVBoxLayout(self)
        title = QLabel("PDF Toolkit")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        desc = QLabel(
            "Info, merge, split, ekstrak, susun ulang, dan rotasi halaman PDF (lokal/offline)."
        )
        desc.setObjectName("pageDesc")
        layout.addWidget(desc)

        tabs = QTabWidget()
        tabs.addTab(self._build_info_tab(), "Info")
        tabs.addTab(self._build_merge_tab(), "Merge")
        tabs.addTab(self._build_split_tab(), "Split")
        tabs.addTab(self._build_extract_tab(), "Ekstrak")
        tabs.addTab(self._build_reorder_tab(), "Susun Ulang")
        tabs.addTab(self._build_rotate_tab(), "Rotasi")
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
        self.info_selector = FileSelector(multi=False, filter=_PDF_FILTER)
        v.addWidget(self.info_selector)
        btn = QPushButton("Tampilkan Informasi")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)
        path = Path()

        def work() -> JobResult:
            files = [Path(f) for f in self.info_selector.files()]
            if not files:
                return JobResult(success=False, error="Pilih satu file PDF terlebih dahulu.")
            info = processor.get_pdf_info(files[0])
            lines = [
                f"Nama file       : {info.path.name}",
                f"Lokasi          : {info.path}",
                f"Ukuran file     : {info.size_bytes} byte",
                f"Jumlah halaman  : {info.page_count if info.page_count is not None else 'Tidak tersedia'}",
                f"Terenskripsi    : {'Ya' if info.encrypted else 'Tidak'}",
                f"Perlu kata sandi: {'Ya' if info.needs_password else 'Tidak'}",
                f"Judul           : {info.title or 'Tidak tersedia'}",
                f"Penulis         : {info.author or 'Tidak tersedia'}",
                f"Subjek          : {info.subject or 'Tidak tersedia'}",
                f"Kata kunci      : {info.keywords or 'Tidak tersedia'}",
                f"Produsen        : {info.producer or 'Tidak tersedia'}",
                f"Dibuat oleh     : {info.creator or 'Tidak tersedia'}",
                f"Tanggal dibuat  : {info.creation_date or 'Tidak tersedia'}",
                f"Tanggal diubah  : {info.mod_date or 'Tidak tersedia'}",
            ]
            if info.page_size:
                lines.append(
                    f"Ukuran halaman 1: {info.page_size[0]} x {info.page_size[1]} pt"
                )
                if info.uniform_page_size is not None:
                    lines.append(
                        "Ukuran seragam  : " + ("Ya" if info.uniform_page_size else "Tidak")
                    )
            if info.metadata_error:
                lines.append(f"Catatan         : {info.metadata_error}")
            return JobResult(success=True, data={"info": info, "text": "\n".join(lines)})

        def done(result: JobResult) -> None:
            if result.success:
                _show(view, result.data.get("text", "Selesai."), True)
            else:
                _show(view, result.error or "Gagal.", False)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    def _build_merge_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.merge_selector = FileSelector(multi=True, filter=_PDF_FILTER)
        v.addWidget(self.merge_selector)

        v.addWidget(QLabel("Urutan file (gunakan tombol untuk mengatur):"))
        row = QHBoxLayout()
        self.merge_list = QListWidget()
        row.addWidget(self.merge_list, 1)
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

        v.addWidget(QLabel("Folder tujuan:"))
        self.merge_out = FolderSelector()
        v.addWidget(self.merge_out)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Nama file hasil:"))
        self.merge_name = QLineEdit("gabungan.pdf")
        name_row.addWidget(self.merge_name, 1)
        v.addLayout(name_row)

        btn = QPushButton("Gabungkan PDF")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        self.merge_selector.files_changed.connect(self._populate_merge_list)

        def move(delta: int) -> None:
            i = self.merge_list.currentRow()
            j = i + delta
            if i < 0 or j < 0 or j >= self.merge_list.count():
                return
            item = self.merge_list.takeItem(i)
            self.merge_list.insertItem(j, item)
            self.merge_list.setCurrentRow(j)

        def remove_selected() -> None:
            i = self.merge_list.currentRow()
            if i >= 0:
                self.merge_list.takeItem(i)

        up.clicked.connect(lambda: move(-1))
        down.clicked.connect(lambda: move(1))
        remove.clicked.connect(remove_selected)

        def work() -> JobResult:
            files = [
                Path(self.merge_list.item(i).data(Qt.UserRole))
                for i in range(self.merge_list.count())
            ]
            out_dir = self.merge_out.folder()
            if len(files) < 2:
                return JobResult(success=False, error="Pilih minimal dua file PDF.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            res = processor.merge_pdfs(files, out_dir, output_name=self.merge_name.text().strip() or None)
            text = (
                f"Berhasil menggabungkan {len(res.inputs)} file.\n"
                f"Jumlah halaman hasil: {res.page_count}\n"
                f"Disimpan di: {res.output}"
            )
            return JobResult(success=True, data={"text": text, "output": res.output})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    def _populate_merge_list(self, files: List[Path]) -> None:
        self.merge_list.clear()
        for f in files:
            item = self.merge_list.addItem(str(f))
            self.merge_list.item(self.merge_list.count() - 1).setData(Qt.UserRole, str(f))
    def _build_split_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.split_selector = FileSelector(multi=False, filter=_PDF_FILTER)
        v.addWidget(self.split_selector)

        self.split_range_radio = QRadioButton("Berdasarkan rentang halaman (contoh: 1-3, 4-7)")
        self.split_each_radio = QRadioButton("Satu halaman per file")
        self.split_range_radio.setChecked(True)
        group = QButtonGroup(w)
        group.addButton(self.split_range_radio)
        group.addButton(self.split_each_radio)
        v.addWidget(self.split_range_radio)
        v.addWidget(self.split_each_radio)

        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Rentang:"))
        self.split_ranges = QLineEdit()
        self.split_ranges.setPlaceholderText("1-3, 4-7, 8-10")
        range_row.addWidget(self.split_ranges, 1)
        v.addLayout(range_row)

        v.addWidget(QLabel("Folder tujuan:"))
        self.split_out = FolderSelector()
        v.addWidget(self.split_out)

        btn = QPushButton("Pisahkan PDF")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def toggle(value: bool) -> None:
            self.split_ranges.setEnabled(self.split_range_radio.isChecked())

        self.split_range_radio.toggled.connect(toggle)

        def work() -> JobResult:
            files = [Path(f) for f in self.split_selector.files()]
            out_dir = self.split_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file PDF.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            if self.split_each_radio.isChecked():
                res = processor.split_each_page(files[0], out_dir)
            else:
                info = processor.get_pdf_info(files[0])
                if not info.page_count:
                    return JobResult(success=False, error="Jumlah halaman tidak tersedia (PDF mungkin terenkripsi).")
                ranges = processor.parse_page_ranges(self.split_ranges.text(), info.page_count)
                res = processor.split_by_ranges(files[0], ranges, out_dir)
            lines = [f"Berhasil membuat {len(res.outputs)} file:"]
            for sf in res.outputs:
                lines.append(f"  - {sf.output.name} (halaman {sf.start}-{sf.end})")
            lines.append(f"Folder: {res.outputs[0].output.parent if res.outputs else out_dir}")
            return JobResult(success=True, data={"text": "\n".join(lines)})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    def _build_extract_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.extract_selector = FileSelector(multi=False, filter=_PDF_FILTER)
        v.addWidget(self.extract_selector)

        row = QHBoxLayout()
        row.addWidget(QLabel("Halaman (contoh: 3, 1, 5-7):"))
        self.extract_pages = QLineEdit()
        row.addWidget(self.extract_pages, 1)
        v.addLayout(row)

        v.addWidget(QLabel("Folder tujuan:"))
        self.extract_out = FolderSelector()
        v.addWidget(self.extract_out)

        btn = QPushButton("Ekstrak Halaman")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def work() -> JobResult:
            files = [Path(f) for f in self.extract_selector.files()]
            out_dir = self.extract_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file PDF.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            info = processor.get_pdf_info(files[0])
            if not info.page_count:
                return JobResult(success=False, error="Jumlah halaman tidak tersedia (PDF mungkin terenkripsi).")
            pages = processor.parse_pages(self.extract_pages.text(), info.page_count)
            res = processor.extract_pages(files[0], pages, out_dir)
            text = (
                f"Berhasil mengekstrak {res.page_count} halaman (urutan: {res.requested_pages}).\n"
                f"Disimpan di: {res.output}"
            )
            return JobResult(success=True, data={"text": text})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    def _build_reorder_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.reorder_selector = FileSelector(multi=False, filter=_PDF_FILTER)
        v.addWidget(self.reorder_selector)

        row = QHBoxLayout()
        row.addWidget(QLabel("Urutan baru (contoh: 3,1,2):"))
        self.reorder_order = QLineEdit()
        row.addWidget(self.reorder_order, 1)
        v.addLayout(row)

        v.addWidget(QLabel("Folder tujuan:"))
        self.reorder_out = FolderSelector()
        v.addWidget(self.reorder_out)

        btn = QPushButton("Simpan Urutan Baru")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def work() -> JobResult:
            files = [Path(f) for f in self.reorder_selector.files()]
            out_dir = self.reorder_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file PDF.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            info = processor.get_pdf_info(files[0])
            if not info.page_count:
                return JobResult(success=False, error="Jumlah halaman tidak tersedia (PDF mungkin terenkripsi).")
            order = processor.parse_pages(self.reorder_order.text(), info.page_count)
            res = processor.reorder_pages(files[0], order, out_dir)
            text = (
                f"Berhasil menyusun ulang {res.page_count} halaman.\n"
                f"Urutan: {res.order}\nDisimpan di: {res.output}"
            )
            return JobResult(success=True, data={"text": text})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w

    def _build_rotate_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.rotate_selector = FileSelector(multi=False, filter=_PDF_FILTER)
        v.addWidget(self.rotate_selector)

        angle_row = QHBoxLayout()
        angle_row.addWidget(QLabel("Sudut:"))
        self.rotate_angle = QComboBox()
        self.rotate_angle.addItems(["90", "180", "270"])
        angle_row.addWidget(self.rotate_angle)
        angle_row.addStretch()
        v.addLayout(angle_row)

        self.rotate_all = QCheckBox("Semua halaman")
        self.rotate_all.setChecked(True)
        v.addWidget(self.rotate_all)

        pages_row = QHBoxLayout()
        pages_row.addWidget(QLabel("Halaman (contoh: 1-3, 5):"))
        self.rotate_pages = QLineEdit()
        self.rotate_pages.setEnabled(False)
        pages_row.addWidget(self.rotate_pages, 1)
        v.addLayout(pages_row)

        self.rotate_all.toggled.connect(lambda on: self.rotate_pages.setEnabled(not on))

        v.addWidget(QLabel("Folder tujuan:"))
        self.rotate_out = FolderSelector()
        v.addWidget(self.rotate_out)

        btn = QPushButton("Terapkan Rotasi")
        v.addWidget(btn, alignment=Qt.AlignLeft)
        view = _result_view()
        v.addWidget(view, 1)

        def work() -> JobResult:
            files = [Path(f) for f in self.rotate_selector.files()]
            out_dir = self.rotate_out.folder()
            if not files:
                return JobResult(success=False, error="Pilih satu file PDF.")
            if out_dir is None:
                return JobResult(success=False, error="Pilih folder tujuan terlebih dahulu.")
            angle = int(self.rotate_angle.currentText())
            info = processor.get_pdf_info(files[0])
            if not info.page_count:
                return JobResult(success=False, error="Jumlah halaman tidak tersedia (PDF mungkin terenkripsi).")
            if self.rotate_all.isChecked():
                pages = list(range(1, info.page_count + 1))
            else:
                ranges = processor.parse_page_ranges(self.rotate_pages.text(), info.page_count)
                pages = [n for s, e in ranges for n in range(s, e + 1)]
            res = processor.rotate_pages(files[0], pages, angle, out_dir)
            text = (
                f"Berhasil memutar {len(res.pages)} halaman sebesar {res.angle} derajat.\n"
                f"Disimpan di: {res.output}"
            )
            return JobResult(success=True, data={"text": text})

        def done(result: JobResult) -> None:
            _show(view, result.data.get("text", "") if result.success else (result.error or "Gagal."), result.success)

        btn.clicked.connect(lambda: self._run(btn, work, done))
        return w
