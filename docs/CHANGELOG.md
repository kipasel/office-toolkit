# CHANGELOG.md

Format mengikuti prinsip Keep a Changelog; versi mengikuti SemVer.

## [0.1.0] — Phase 0 — Audit & Perencanaan

### Added
- `AGENTS.md` — aturan kerja, konvensi, dan environment hasil audit.
- `README.md` — ringkasan proyek dan status Phase 0.
- `docs/SPECIFICATION.md` — spesifikasi teknis tidak ambigu + dependensi diusulkan.
- `docs/ARCHITECTURE.md` — arsitektur lapisan, model job, alur output.
- `docs/FEATURE_MATRIX.md` — matriks seluruh fitur (status awal: NOT IMPLEMENTED).
- `docs/TEST_PLAN.md` — rencana pengujian dan kriteria penerimaan.
- `docs/SECURITY.md` — keamanan, privasi, batas sumber daya, lisensi.
- `docs/CHANGELOG.md` — dokumen ini.

### Notes
- Belum ada kode aplikasi; belum ada dependensi yang dipasang.
- Environment audit: Python 3.12.0 (`py -3.12`), Windows 11 x64.
- Ketersediaan wheel diverifikasi untuk pypdf 6.20.0, qrcode 8.2, zxing-cpp 3.1.1,
  pytest-qt 4.5.0, opencv-python-headless 4.11.0.86 (pembanding).
- Menunggu persetujuan pengguna sebelum Phase 1.

## [0.2.0] — Phase 1 — Foundation, Core Services, UI

### Added
- `src/office_toolkit/bootstrap.py`, `main.py`, `__main__.py`, `__init__.py` (v0.1.0).
- Core: `config.py`, `errors.py`, `logging_config.py`, `file_validation.py`, `output_manager.py`, `job_manager.py`.
- UI: `main_window.py`, `navigation.py`, `dashboard.py`, `ui/components/` (file_selector, folder_selector), `ui/pages/placeholder_page.py`, `ui/styles/theme.py`.
- Tests: `tests/unit/test_smoke.py`, `tests/unit/test_core.py`, `tests/unit/test_job_manager.py`, `tests/ui/test_ui_smoke.py` (18 passed).

### Updated
- `docs/ARCHITECTURE.md`, `docs/FEATURE_MATRIX.md`, `docs/TEST_PLAN.md`, `docs/SECURITY.md`, `docs/CHANGELOG.md`.

## [0.3.0] — Phase 3 — PDF Toolkit Dasar (A1–A7)

### Added
- `src/office_toolkit/services/pdf/processor.py` — info, merge, split (rentang & per halaman),
  extract, reorder, dan rotate halaman berbasis PyMuPDF; validasi halaman, penanganan PDF
  terenkripsi/rusak, dan penulisan output aman (temporer + verifikasi + `os.replace`).
- `src/office_toolkit/services/pdf/ui.py` — halaman PDF Toolkit berbahasa Indonesia dengan enam tab;
  operasi berat dijalankan lewat `JobManager` (UI tidak diblokir).
- `src/office_toolkit/services/pdf/__init__.py` — ekspos `processor`.
- `tests/fixtures/pdf_factory.py` + `tests/conftest.py` — fixture PDF sintetis (berlabel,
  terenkripsi, rusak).
- `tests/unit/test_pdf.py` (43), `tests/integration/test_pdf_integration.py` (2),
  `tests/security/test_pdf_security.py` (11), `tests/ui/test_pdf_ui.py` (3).

### Changed
- `src/office_toolkit/ui/navigation.py` — menambahkan entri "PDF Toolkit" dan signal `page_requested`.
- `src/office_toolkit/ui/main_window.py` — menghubungkan halaman PDF ke `QStackedWidget`.
- `tests/unit/test_job_manager.py` — menunggu sinyal dengan batas waktu (menghilangkan flakiness
  lama; assertion tidak diubah/diperlemah).

### Notes
- Semua operasi memakai PyMuPDF; tidak ada dependensi baru yang dipasang.
- Keterbatasan: bookmark/outline, XMP metadata, dan sebagian struktur formulir tidak dijamin
  dipertahankan oleh merge/split/extract/reorder (dibangun via `insert_pdf`).
- Hasil tes: **81 passed** (59 tes baru Phase 3 + 22 tes regresi Phase 1/Phase 2).
- Status fitur A1–A7: **TESTED** (belum VERIFIED; menunggu verifikasi/penerimaan pengguna).
