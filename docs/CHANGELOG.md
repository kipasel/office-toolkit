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
