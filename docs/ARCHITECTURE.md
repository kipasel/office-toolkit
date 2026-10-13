# ARCHITECTURE.md — Arsitektur Office Toolkit

Versi: 0.5 (Phase 5)
Status: berjalan. Fondasi (Phase 1), PDF Toolkit Dasar (A1–A7), PDF Toolkit Lanjutan (A8–A14),
dan QR Toolkit (C1–C6) IMPLEMENTED/TESTED.

## 1. Prinsip Arsitektur

- **Pemisahan lapisan**: UI, business logic (services), validasi/utilitas inti (core), akses file.
- **Ketergantungan satu arah**: `ui → services → core`. `core` tidak mengimpor `ui`/`services`.
  `services` tidak mengimpor `ui`.
- **Testable**: service dipanggil tanpa UI; fixture sintetis untuk pengujian.
- **Tanpa global mutable state** yang tidak perlu; konfigurasi lewat objek `AppConfig`.
- **Thread-safe UI**: operasi berat dijalankan di worker Qt, komunikasi via signal/slot.
- **Fondasi Phase 1** (IMPLEMENTED): `bootstrap`, `logging_config`, `errors`, `config`, `file_validation`, `output_manager`, `job_manager`, UI minimal + komponen reusable.
- **PDF Toolkit Dasar** (IMPLEMENTED/TESTED): `services/pdf/processor.py` (info, merge, split, extract, reorder, rotate via PyMuPDF) dan `services/pdf/ui.py` (6 tab, worker `JobManager`).
- **PDF Toolkit Lanjutan** (IMPLEMENTED/TESTED): `services/pdf/{common,compress,render,from_images,edit,security}.py` dan `services/pdf/advanced_ui.py` (9 tab, worker `JobManager`).
- **QR Toolkit** (IMPLEMENTED/TESTED): `services/qr/{common,generator,csv_batch,decoder}.py` dan
  `services/qr/ui.py` (3 tab, worker `JobManager`). Generate memakai `qrcode` (PNG/SVG); decode
  memakai OpenCV `QRCodeDetector` (opencv-python-headless) — pengganti zxing-cpp yang diblokir
  Smart App Control pada mesin pengembangan (persetujuan pengguna, lihat SPECIFICATION §12).

## 2. Struktur Direktori (target)

```
office-toolkit/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
├── app.spec
├── docs/
│   ├── SPECIFICATION.md
│   ├── ARCHITECTURE.md
│   ├── FEATURE_MATRIX.md
│   ├── TEST_PLAN.md
│   ├── SECURITY.md
│   └── CHANGELOG.md
├── assets/
│   ├── icons/
│   └── fonts/
├── scripts/
│   ├── dev_setup.ps1
│   ├── run_tests.ps1
│   └── build_windows.ps1
├── src/office_toolkit/
│   ├── __init__.py
│   ├── __main__.py          # entry: python -m office_toolkit
│   ├── main.py              # entry point aplikasi
│   ├── bootstrap.py         # inisialisasi konfigurasi, logging, exception hook
│   ├── core/
│   │   ├── config.py        # AppConfig + batas sumber daya
│   │   ├── errors.py        # hierarki exception
│   │   ├── file_validation.py
│   │   ├── output_manager.py
│   │   ├── job_manager.py
│   │   └── logging_config.py
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── navigation.py
│   │   ├── dashboard.py
│   │   ├── components/      # widget generik (file picker, preview, progress)
│   │   ├── dialogs/         # dialog konfirmasi/error
│   │   ├── pages/           # satu halaman per fitur
│   │   └── styles/          # QSS lokal + ikon
│   ├── services/
│   │   ├── pdf/
│   │   ├── images/
│   │   ├── qr/
│   │   ├── files/
│   │   └── documents/
│   └── resources/           # resource Python (ikon QRC/paths)
└── tests/
    ├── unit/
    ├── integration/
    ├── ui/
    ├── security/
    └── fixtures/
```

Aturan: bukan satu file besar; setiap service punya tanggung jawab tunggal dan dapat diuji sendiri.

## 3. Lapisan dan Tanggung Jawab

### core
- `config.py` — `AppConfig` (dataclass) memuat batas sumber daya, direktori temp, preferensi output.
- `errors.py` — hierarki: `OfficeToolkitError` → `ValidationError`, `DecodeError`,
  `ProcessingError`, `OutputError`, `PasswordError`, `ResourceLimitError`, `CancelledError`.
- `file_validation.py` — cek eksistensi, kosong, rusak, ekstensi vs konten, keterbacaan, path ilegal,
  benturan nama, batas ukuran.
- `output_manager.py` — tulis ke file temporer di direktori tujuan, lalu `os.replace` atomik ke nama
  final; bersihkan temporer saat gagal; cegah timpa tanpa izin.
- `job_manager.py` — definisi job, status, progres nyata, pembatalan via token; tidak menyentuh UI.
- `logging_config.py` — logging lokal ke file, rotasi, redaksi path/secret.

### services
- `pdf/` — **Dasar** `processor.py` (info, merge, split, extract, reorder, rotate) **IMPLEMENTED**
  (Phase 3). **Lanjutan** (Phase 4) **IMPLEMENTED**: `common.py` (buka PDF sadar kata sandi,
  tulis terverifikasi, resolusi halaman, nama aman, rumus penghematan, batas render),
  `compress.py` (struktur/images/rasterize), `render.py` (PDF→PNG/JPEG),
  `from_images.py` (gambar→PDF), `edit.py` (teks, gambar, anotasi, tanda tangan gambar),
  `security.py` (proteksi & buka proteksi). `advanced_ui.py` menyediakan 9 tab UI.
  Aturan: validasi → proses (PyMuPDF) → tulis lewat `OutputManager` (temporer + verifikasi +
  `os.replace`) → kembalikan hasil terstruktur. Dokumen baru dibentuk via `insert_pdf` (termasuk
  rebuild pada buka proteksi), sehingga outline/metadata tidak dijamin dipertahankan (kecuali
  rotate yang memodifikasi salinan).
- `images/` — `convert`, `resize`, `compress`, `target_size`, `crop`, `rotate`, `batch`,
  `strip_metadata`, `exif`.
- `qr/` — **IMPLEMENTED** (Phase 5): `common.py` (validasi input, warna `#RRGGBB`, kontras WCAG,
  path output aman, tulis terverifikasi), `generator.py` (generate PNG/SVG C1–C4), `csv_batch.py`
  (batch CSV C5), `decoder.py` (baca QR C6). `ui.py` menyediakan 3 tab (Buat QR, Batch CSV, Baca
  QR). Aturan: validasi → proses (qrcode/OpenCV) → tulis lewat `OutputManager` (temporer +
  verifikasi + `os.replace`) → kembalikan hasil terstruktur dengan peringatan. Payload QR tidak
  pernah di-log dan URL tidak dibuka otomatis.
- `files/` — `batch_rename`, `duplicate_scan`, `list_directory`, `format_text/csv/json`,
  `document_photo`, `history`.
- `documents/` — pembersihan/formating teks ringan (bukan konversi dokumen penuh).

Setiap fungsi service: validasi input → proses → tulis via `OutputManager` → kembalikan hasil
terstruktur (`Result` dengan path, ukuran, peringatan).

### ui
- `main_window.py` — shell: sidebar + stacked workspace.
- `navigation.py` — sidebar, kategori.
- `dashboard.py` — pencarian tool + kartu kategori.
- `pages/` — satu halaman per fitur; hanya memanggil service via worker.
- `components/` — `FileSelector`, `FolderSelector`, `ResultPreview`, `ProgressPanel`, `StatusBadge`.
- `styles/` — QSS lokal, ikon/font lokal.

## 4. Model Eksekusi Job

```
UI (main thread)
  → membuat JobSpec (input, output, opsi)
  → Worker(QObject) dipindah ke QThread
      → memanggil service (blocking, murni Python)
      → emit progress(int), finished(Result), failed(Exception), cancelled()
  → UI memperbarui widget via signal/slot
```

Aturan:
- Worker **tidak** menyentuh widget Qt secara langsung.
- Progres hanya bila dapat dihitung; jika tidak, pakai busy indicator (tanpa persentase palsu).
- Pembatalan memakai flag/token; output sementara dibersihkan; tidak meninggalkan output korup
  yang tampak berhasil.

## 5. Alur Output & Keamanan File

1. Validasi input (`file_validation`).
2. Tentukan direktori output (dipilih pengguna atau default).
3. Tulis ke `tmp` di direktori tujuan (atau temp app bila lintas volume).
4. Verifikasi hasil (buka ulang bila memungkinkan).
5. `os.replace` atomik ke nama final.
6. Pada kegagalan/pembatalan: hapus temporer.
7. Jangan pernah menghapus input.

## 6. Kebijakan Dependensi per Modul

| Kebutuhan | Library | Catatan |
|---|---|---|
| Manipulasi/rendering PDF | PyMuPDF | Rendering gambar, anotasi, teks/gambar |
| Operasi struktural PDF | pypdf | Merge/split/rotate berbasis objek, enkripsi ringan |
| Gambar | Pillow | Konversi, resize, EXIF, transparansi |
| Generate QR | qrcode | PNG via Pillow, SVG via `qrcode.image.svg` |
| Decode QR | opencv-python-headless | `QRCodeDetector`; pengganti zxing-cpp (diblokir Smart App Control) |
| UI | PySide6 | Qt 6 |
| Tes | pytest, pytest-qt | Fixture sintetis |
| Build | PyInstaller | onedir default |

## 7. Risiko Arsitektur

- **AGPL PyMuPDF** memengaruhi model distribusi (lihat SECURITY/SPECIFICATION).
- **opencv-python-headless** lebih besar daripada zxing-cpp, tetapi terverifikasi dapat memuat &
  mendekode QR pada mesin pengembangan (zxing-cpp diblokir Smart App Control). Cakupan decode tetap
  perlu diuji terhadap kasus nyata (barcode 1D tidak didukung).
- Qt packaging (plugin platform, styles) perlu diuji pada build.
- Operasi PDF yang menulis ulang dapat menghilangkan bookmark/form/tautan; perlu peringatan dan
  pemilihan operasi struktural (pypdf) bila akan mempertahankan struktur.
