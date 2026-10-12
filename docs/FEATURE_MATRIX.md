# FEATURE_MATRIX.md — Matriks Fitur & Status

Status: 0.1 (Phase 0 — status awal)
Legenda status: **NOT IMPLEMENTED** · **IMPLEMENTED** · **TESTED** · **VERIFIED** · **BLOCKED**
Legenda tes: `—` belum ada.

> Semua fitur di bawah berstatus **NOT IMPLEMENTED** pada akhir Phase 0. Tidak ada kode aplikasi
> yang ditulis pada Phase 0.

## Fondasi (Phase 1)

| ID | Fitur | Status | Tes | Catatan |
|---|---|---|---|---|
| F1 | Konfigurasi proyek (pyproject, requirements) | IMPLEMENTED | TESTED | Phase 1 — 15 unit+UI tests lulus |
| F2 | Entry point & bootstrap | IMPLEMENTED | TESTED | Phase 1 |
| F3 | Logging lokal + redaksi | IMPLEMENTED | TESTED | Phase 1 |
| F4 | Hierarki error | IMPLEMENTED | TESTED | Phase 1 |
| F5 | Validasi file | IMPLEMENTED | TESTED | Phase 1 |
| F6 | Output manager | IMPLEMENTED | TESTED | Phase 1 |
| F7 | Job manager + worker Qt | IMPLEMENTED | TESTED | Phase 1 |
| F8 | Main window + navigasi + dashboard | IMPLEMENTED | TESTED | Phase 1 |
| F9 | Komponen UI dasar | IMPLEMENTED | TESTED | FileSelector, FolderSelector, PlaceholderPage, Theme |

## Modul A — PDF Toolkit (Phase 2)

| ID | Fitur | Status | Tes | Catatan |
|---|---|---|---|---|
| A1 | Info PDF (metadata, halaman, ukuran) | NOT IMPLEMENTED | — | |
| A2 | Merge PDF (urutan dapat diubah) | NOT IMPLEMENTED | — | |
| A3 | Split berdasarkan rentang | NOT IMPLEMENTED | — | |
| A4 | Split per halaman | NOT IMPLEMENTED | — | |
| A5 | Extract halaman | NOT IMPLEMENTED | — | |
| A6 | Reorder halaman | NOT IMPLEMENTED | — | |
| A7 | Rotate halaman | NOT IMPLEMENTED | — | |
| A8 | Tambah teks & gambar | NOT IMPLEMENTED | — | |
| A9 | Anotasi dasar | NOT IMPLEMENTED | — | |
| A10 | Tanda tangan gambar + pratinjau | NOT IMPLEMENTED | — | |
| A11 | PDF → PNG/JPEG (DPI) | NOT IMPLEMENTED | — | |
| A12 | Gambar → PDF | NOT IMPLEMENTED | — | |
| A13 | Proteksi kata sandi | NOT IMPLEMENTED | — | |
| A14 | Buka proteksi (kata sandi diketahui) | NOT IMPLEMENTED | — | |

## Modul B — Image Toolkit (Phase 3)

| ID | Fitur | Status | Tes | Catatan |
|---|---|---|---|---|
| B1 | Konversi format | NOT IMPLEMENTED | — | |
| B2 | Resize (piksel/persentase) | NOT IMPLEMENTED | — | |
| B3 | Compress (kualitas) | NOT IMPLEMENTED | — | |
| B4 | Target ukuran file (KB) | NOT IMPLEMENTED | — | |
| B5 | Crop manual | NOT IMPLEMENTED | — | |
| B6 | Rotate | NOT IMPLEMENTED | — | |
| B7 | Batch convert & resize | NOT IMPLEMENTED | — | |
| B8 | Hapus metadata | NOT IMPLEMENTED | — | |
| B9 | Pratinjau & ukuran sebelum/sesudah | NOT IMPLEMENTED | — | |
| B10 | Penanganan transparansi | NOT IMPLEMENTED | — | |
| B11 | Orientasi EXIF | NOT IMPLEMENTED | — | |

## Modul C — QR Code (Phase 4)

| ID | Fitur | Status | Tes | Catatan |
|---|---|---|---|---|
| C1 | Generate QR (teks/URL/nomor) | NOT IMPLEMENTED | — | |
| C2 | Pengaturan ukuran/margin/warna/ECC | NOT IMPLEMENTED | — | |
| C3 | Logo opsional + peringatan | NOT IMPLEMENTED | — | |
| C4 | Ekspor PNG & SVG | NOT IMPLEMENTED | — | |
| C5 | Generate massal dari CSV | NOT IMPLEMENTED | — | |
| C6 | Baca QR dari gambar lokal | NOT IMPLEMENTED | — | |

## Modul D — File Utilities (Phase 4)

| ID | Fitur | Status | Tes | Catatan |
|---|---|---|---|---|
| D1 | Batch rename (awalan/akhiran/pola/nomor) | NOT IMPLEMENTED | — | |
| D2 | Pratinjau rename | NOT IMPLEMENTED | — | |
| D3 | Deteksi duplikat (SHA-256) | NOT IMPLEMENTED | — | |
| D4 | Ekspor daftar file ke CSV | NOT IMPLEMENTED | — | |
| D5 | Format TXT/CSV/JSON | NOT IMPLEMENTED | — | |
| D6 | Foto dokumen (crop/rotate/kontras) | NOT IMPLEMENTED | — | |
| D7 | Ekspor foto dokumen → PDF | NOT IMPLEMENTED | — | |
| D8 | Pilih folder output | NOT IMPLEMENTED | — | |
| D9 | Riwayat operasi lokal | NOT IMPLEMENTED | — | |

## Hardening & Distribusi (Phase 5)

| ID | Item | Status | Catatan |
|---|---|---|---|
| H1 | Audit matriks fitur | NOT IMPLEMENTED | |
| H2 | Tes regresi | NOT IMPLEMENTED | |
| H3 | Audit privasi & jaringan | NOT IMPLEMENTED | |
| H4 | Tes penggunaan memori | NOT IMPLEMENTED | |
| H5 | Perbaikan UX | NOT IMPLEMENTED | |
| H6 | Audit lisensi | NOT IMPLEMENTED | |
| H7 | Build executable Windows | NOT IMPLEMENTED | |
| H8 | Tes executable hasil build | NOT IMPLEMENTED | |
| H9 | Dokumentasi penggunaan & distribusi | NOT IMPLEMENTED | |

## Di Luar Ruang Lingkup

- OCR
- Cloud storage / sinkronisasi
- Tanda tangan digital tersertifikasi
- Barcode satu dimensi (1D)
- Konversi dokumen penuh (DOCX dsb.) dengan pemeliharaan struktur
