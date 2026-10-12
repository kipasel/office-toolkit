# Office Toolkit

Aplikasi desktop Windows yang mengolah **PDF, gambar, QR Code, dan utilitas file kantor**.
Semua fitur inti berjalan **lokal/offline** dan **tanpa telemetry**.

> **Status: PHASE 1 — Foundation & UI (IMPLEMENTED).**
> Fondasi aplikasi dan UI siap. Modul pemrosesan (PDF/Image/QR/Utilities) akan diimplementasikan pada fase berikutnya.

## Ruang Lingkup

- **Modul A — PDF Toolkit**: kompres, merge, split, extract, reorder, rotate, tambah teks/gambar/
  anotasi/tanda tangan gambar, PDF↔gambar, proteksi & buka proteksi, info PDF.
- **Modul B — Image Toolkit**: konversi format, resize, compress, target ukuran file, crop, rotate,
  batch, hapus metadata, transparansi & orientasi EXIF.
- **Modul C — QR Code**: generate (teks/URL/nomor), pengaturan warna/margin/ECC, logo opsional,
  ekspor PNG/SVG, generate massal dari CSV, baca QR dari gambar lokal.
- **Modul D — File Utilities**: batch rename (dengan pratinjau), deteksi duplikat SHA-256, ekspor
  daftar file ke CSV, format TXT/CSV/JSON, pengolahan foto dokumen, riwayat operasi lokal.

Di luar ruang lingkup versi pertama: OCR, cloud storage, sinkronisasi, tanda tangan digital
tersertifikasi, barcode 1D.

## Dokumentasi

| Dokumen | Isi |
|---|---|
| `AGENTS.md` | Aturan kerja dan konvensi |
| `docs/SPECIFICATION.md` | Spesifikasi teknis & dependensi terkunci |
| `docs/ARCHITECTURE.md` | Arsitektur, lapisan, dan struktur modul |
| `docs/FEATURE_MATRIX.md` | Daftar fitur dan status |
| `docs/TEST_PLAN.md` | Rencana tes & kriteria penerimaan |
| `docs/SECURITY.md` | Validasi, sumber daya, privasi |
| `docs/CHANGELOG.md` | Riwayat perubahan |

## Environment

- Windows 10/11 64-bit
- Python 3.12 (`py -3.12`)
- Lihat `docs/SPECIFICATION.md` untuk versi dependensi terkunci.

## Menjalankan (setelah Phase 1)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python -m office_toolkit
```

Perintah ini akan berfungsi setelah entry point dibuat pada Phase 1.
