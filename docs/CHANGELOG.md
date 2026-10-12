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
