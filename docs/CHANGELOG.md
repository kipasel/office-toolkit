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

## [0.4.0] — Phase 4 — PDF Toolkit Lanjutan (A8–A14)

### Added
- `src/office_toolkit/services/pdf/common.py` — helper bersama: buka PDF (sadar kata sandi, tanpa
  password di pesan), tulis PDF/gambar hasil terverifikasi, resolusi halaman, nama output aman,
  rumus `savings_pct`, batas render (DPI & jumlah halaman).
- `src/office_toolkit/services/pdf/compress.py` — Fitur A: kompresi mode `struktur` (lossless),
  `images` (lossy `rewrite_images`), `rasterize` (dengan peringatan eksplisit).
- `src/office_toolkit/services/pdf/render.py` — Fitur B: render PDF→PNG/JPEG per halaman,
  `_page_00N`, batas DPI 36–600, laporan gagal per halaman.
- `src/office_toolkit/services/pdf/from_images.py` — Fitur C: gambar→PDF (A4/Letter/ukuran gambar,
  orientasi, transparansi, EXIF, frame-1 TIFF/GIF dengan peringatan, gambar rusak per-file).
- `src/office_toolkit/services/pdf/edit.py` — Fitur D–G: tambah teks (kotak teks, fallback font
  Unicode), tambah gambar (rasio aspek dipertahankan, dibatasi agar tak keluar halaman), anotasi
  (highlight tanpa highlight palsu, note, rect, line/arrow), dan tanda tangan gambar (dengan
  peringatan BUKAN tanda tangan digital).
- `src/office_toolkit/services/pdf/security.py` — Fitur H–I: proteksi AES-256/128 dengan izin
  dokumen; buka proteksi hanya dengan kata sandi diketahui (rebuild dokumen, tidak pernah cracking).
- `src/office_toolkit/services/pdf/advanced_ui.py` — halaman "PDF Lanjutan" berbahasa Indonesia,
  9 tab; operasi berat lewat `JobManager`; konfirmasi untuk rasterize, tanda tangan, dan buka proteksi.
- `src/office_toolkit/core/config.py` — batas DPI render (`pdf_render_dpi_min=36`,
  `pdf_render_dpi_max=600`).
- Tests: `tests/unit/test_pdf_compress.py` (10), `test_pdf_render.py` (9), `test_pdf_from_images.py`
  (12), `test_pdf_edit.py` (10), `test_pdf_annotate.py` (9), `test_pdf_security_advanced.py` (10),
  `tests/security/test_pdf_advanced_security.py` (7), `tests/integration/test_pdf_advanced_integration.py`
  (2), `tests/ui/test_pdf_advanced_ui.py` (3).

### Changed
- `src/office_toolkit/services/pdf/__init__.py` — ekspos `compress`, `edit`, `from_images`,
  `processor`, `render`, `security`.
- `src/office_toolkit/ui/navigation.py` — entri "PDF Lanjutan".
- `src/office_toolkit/ui/main_window.py` — `PdfAdvancedPage` di stack (index 2).
- `tests/ui/test_pdf_ui.py` — navigasi kini mengecek 3 halaman (regresi 2→3, diperbarui jujur).
- `tests/fixtures/pdf_factory.py` — helper `make_pdf_with_image`.
- `docs/FEATURE_MATRIX.md` (0.4), `docs/TEST_PLAN.md` (0.4, §5.2b), `docs/SECURITY.md` (5b),
  `docs/CHANGELOG.md`.

### Notes
- Kendala PyMuPDF 1.28.x yang dihindari: membaca `doc.needs_pass` setelah `authenticate`
  merusak saluran konten; status proteksi diambil lewat probe terpisah, dan `decrypt` rebuild
  halaman ke dokumen baru (bookmark/metadata tidak dijamin).
- `pytest-qt` tetap belum terpasang; tes UI memakai `QApplication` offscreen manual.
- Hasil tes: **156 passed, 1 warning** (74 tes baru Phase 4 + 82 tes regresi).
- Status fitur A8–A14: **TESTED** (belum VERIFIED; menunggu verifikasi/penerimaan pengguna).

## [0.5.0] — Phase 5 — QR Toolkit (C1–C6)

### Added
- `src/office_toolkit/services/qr/common.py` — helper bersama: batas ukuran input, validasi tabel
  CSV, warna `#RRGGBB`, rasio kontras WCAG (ambang 3.0), path output aman, penulisan terverifikasi
  (temporer → verifikasi → `os.replace`).
- `src/office_toolkit/services/qr/generator.py` — Fitur C1–C4: generate QR (teks/URL/nomor) dengan
  `qrcode`, desain (box_size, quiet zone, warna, ECC L/M/Q/H), logo tengah opsional (fraksi ≤ 30%,
  peringatan keterbacaan), ekspor PNG (verifikasi reopen Pillow) dan SVG (parse XML; logo ditolak
  dengan error jelas).
- `src/office_toolkit/services/qr/csv_batch.py` — Fitur C5: batch CSV (UTF-8 ± BOM), kolom isi +
  nama opsional, progress callback, kegagalan per baris fisik, sanitasi nama & anti-traversal,
  anti-overwrite, `preview_csv` untuk UI.
- `src/office_toolkit/services/qr/decoder.py` — Fitur C6: baca QR dari gambar lokal via OpenCV
  `QRCodeDetector` (opencv-python-headless), multi-QR, guard timeout
  (`qr_decode_timeout_sec`) & batas piksel; payload tidak pernah di-log/dibuka.
- `src/office_toolkit/services/qr/ui.py` + `src/office_toolkit/services/qr/__init__.py` —
  halaman "QR Toolkit" berbahasa Indonesia: tab "Buat QR" (pratinjau asli + ekspor), "Batch dari
  CSV" (pemilih kolom, progress), "Baca QR".
- `tests/fixtures/qr_factory.py` — fixture QR/gambar/logo/CSV sintetis.
- Tests: `tests/unit/test_qr_generator.py` (14), `test_qr_export.py` (13), `test_qr_logo.py` (6),
  `test_qr_csv.py` (17), `test_qr_decoder.py` (10), `tests/security/test_qr_security.py` (10),
  `tests/integration/test_qr_integration.py` (4), `tests/ui/test_qr_ui.py` (8). Total 82.

### Changed
- **Keputusan dependensi (disetujui pengguna):** `zxing-cpp` diganti `opencv-python-headless`
  (`4.11.0.86`) + `numpy` (`2.5.4`) karena import `.pyd` zxing-cpp diblokir Smart App Control pada
  mesin pengembangan (lihat SPECIFICATION §3.3/§12). `qrcode==8.2` ditambahkan.
- `requirements.txt`, `pyproject.toml` — pembaruan manifest dependensi.
- `src/office_toolkit/ui/navigation.py` — entri "QR Toolkit" (index 3).
- `src/office_toolkit/ui/main_window.py` — `QrToolkitPage` ditambahkan ke stack.
- `tests/ui/test_pdf_ui.py`, `tests/ui/test_pdf_advanced_ui.py` — navigasi mengecek 4 halaman
  (regresi 3→4, diperbarui jujur).
- `docs/SPECIFICATION.md` (§3.1/§3.3/§12), `docs/FEATURE_MATRIX.md` (0.5), `docs/TEST_PLAN.md`
  (0.5, §5.2c), `docs/SECURITY.md` (5c & lisensi), `docs/ARCHITECTURE.md`, `README.md`.

### Notes
- QR berlogo **TIDAK dijamin** tetap dapat dipindai (peringatan eksplisit di UI & output).
- Ekspor SVG menolak logo (error eksplisit, bukan drop diam-diam).
- Decoder mengganti zxing-cpp karena Smart App Control (`SmartAppControlState: On`) memblokir DLL;
  implementasi fallback OpenCV diverifikasi membaca QR round-trip sebelum dipakai.
- Hasil tes: **238 passed, 3 warnings** (82 tes baru Phase 5 + 156 tes regresi; 2 warning sporadic
  libpyside + 1 `qt_api`).
- Status fitur C1–C6: **TESTED** (belum VERIFIED; menunggu verifikasi/penerimaan pengguna).

## [0.7.0] — Metro UI Redesign (Visual)

### Added
- `src/office_toolkit/ui/styles/tokens.py` — token desain tunggal (warna, spasi, radius,
  tipografi, warna kategori). Semua QSS komponen membaca dari sini.
- `src/office_toolkit/ui/styles/icons.py` — pabrik ikon berbasis `QPainter` (tanpa aset biner,
  tanpa dependensi baru): `icon()`, `pixmap()`, `app_logo()`, `app_icon()`.
- `src/office_toolkit/ui/tools.py` — registri alat (29 entri) sebagai sumber tunggal untuk
  petak dasbor dan pencarian; entri yang belum ada ditandai `available=False`.
- `src/office_toolkit/ui/components/tile.py` — `MetroTile` (petak berwarna, fokus keyboard,
  keadaan "BELUM TERSEDIA" untuk fitur yang belum dibuat).
- `src/office_toolkit/ui/components/header.py` — `Header` (judul/deskripsi halaman, pencarian
  alat global, lencana status offline).
- `tests/ui/test_metro_ui.py` (9) — petak untuk setiap alat, filter pencarian, keadaan kosong,
  sinyal klik petak, item sidebar non-aktif, pencarian memindah ke dasbor, ikon jendela.

### Changed
- `src/office_toolkit/ui/styles/theme.py` — QSS dibangun dari token; `apply_theme()` memasang gaya
  Fusion, font Metro, stylesheet, dan ikon jendela. **Sebelumnya QSS ada tetapi tidak pernah dipakai.**
- `src/office_toolkit/ui/navigation.py` — sidebar bergaya Metro: blok merek, 5 entri halaman
  berikon, bagian "Segera Hadir" non-aktif, footer versi/offline. API `page_requested`,
  `setCurrentRow`, `currentRow` dipertahankan.
- `src/office_toolkit/ui/dashboard.py` — dari label kosong menjadi petak Metro yang dikelompokkan
  per kategori, dengan pencarian nyata (memfilter registri) dan keadaan kosong informatif.
- `src/office_toolkit/ui/main_window.py` — tata letak sidebar + header + `QStackedWidget`;
  petak/panel pencarian terhubung ke halaman & tab nyata; ikon jendela dipasang.
- `src/office_toolkit/bootstrap.py` — memanggil `apply_theme(app)` dan memasang ikon jendela.
- `src/office_toolkit/ui/components/file_selector.py`, `folder_selector.py`,
  `services/{pdf/ui.py,pdf/advanced_ui.py,qr/ui.py,images/ui.py}` — gaya inline ditokenkan
  menjadi `objectName` (`secondaryButton`, `pageTitle`, `hintText`, `warningText`, `previewBox`).
- `tests/ui/test_ui_smoke.py` — `test_dashboard_search_filters` kini benar-benar menguji filter.
- `tests/unit/test_smoke.py` — `test_version_matches_pyproject` membandingkan `__version__`
  dengan `pyproject.toml` (mencegah versi menyimpang lagi).
- `pyproject.toml`, `src/office_toolkit/__init__.py` — versi 0.6.0 → 0.7.0.

### Notes
- Hanya perubahan visual/keterpaduan; tidak ada logika bisnis, arsitektur lapisan, atau dependensi
  baru. Tombol tanpa handler tidak ditambahkan; fitur yang belum ada ditandai eksplisit.
- **Flaky pra-ada (bukan regresi):** `tests/integration/test_qr_integration.py` sebelumnya kadang menabrak
  proses (exit 127) karena interaksi `QThread` (`JobManager`) + OpenCV di bawah capture pytest.
  Crash tersebut diperbaiki di Phase 7 (siklus hidup `JobManager`/`QThread`); tidak lagi teramati dalam
  pengujian berulang.
- Hasil tes: **256 passed, 1 warning** (254+2 regresi baru untuk `JobManager`). Integrasi sekarang stabil.

## [0.6.0] — Image Toolkit (B1/B2/B8) + Sinkronisasi Dokumen

### Added
- `src/office_toolkit/services/images/ui.py` — halaman "Image Toolkit" berbahasa Indonesia dengan
  tiga tab nyata: **Info** (format, dimensi, ukuran, transparansi), **Konversi** (PNG/JPEG/WebP/
  BMP/TIFF, kualitas, opsi hapus metadata), dan **Resize** (lebar jaga rasio aspek atau persentase,
  format keluaran). Operasi berat lewat `JobManager`; memakai ulang `processor` yang sudah ada.
- `tests/ui/test_image_ui.py` (5) — 3 tab, navigasi ke halaman (index 4), dispatch job, info
  dimensi, dan konversi menulis file.
- `tests/unit/test_image.py` — tambah tes hapus metadata (B8) dan penolakan file tidak ada.

### Changed
- `src/office_toolkit/ui/navigation.py` — entri "Image Toolkit" (index 4).
- `src/office_toolkit/ui/main_window.py` — `ImageToolkitPage` ditambahkan ke `QStackedWidget`.
- `tests/ui/test_pdf_ui.py`, `test_pdf_advanced_ui.py`, `test_qr_ui.py` — jumlah halaman stack
  kini 5 (regresi 4→5, diperbarui jujur).
- `docs/FEATURE_MATRIX.md` — Modul B dikoreksi: B1/B2/B8 **IMPLEMENTED + TESTED** (sebelumnya salah
  tertulis NOT IMPLEMENTED meski `processor` sudah ada); status dokumen 0.6.
- `AGENTS.md` — status ringkasan ke Phase 5, QR decode `opencv-python-headless`, environment
  diperbarui (qrcode/opencv/numpy terpasang; pypdf & pytest-qt belum).
- `pyproject.toml` — versi 0.1.0 → 0.6.0 (sinkron dengan changelog).

### Notes
- Modul B belum lengkap: B3/B4/B5/B6/B7/B9/B10/B11 tetap **NOT IMPLEMENTED** dan ditandai eksplisit.
- Hasil tes: **245 passed, 2 warnings** (5 tes UI baru + 2 tes unit baru + 238 regresi).
- Status fitur B1/B2/B8: **TESTED** (belum VERIFIED; menunggu verifikasi/penerimaan pengguna).
