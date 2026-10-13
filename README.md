# Office Toolkit

Aplikasi desktop Windows yang mengolah **PDF, gambar, QR Code, dan utilitas file kantor**.
Semua fitur inti berjalan **lokal/offline** dan **tanpa telemetry**.

> **Status: PHASE 5 — QR Toolkit (IMPLEMENTED, TESTED).**
> Fondasi aplikasi, UI, PDF Toolkit Dasar (info, merge, split, extract, reorder, rotate), PDF
> Toolkit Lanjutan (kompresi, PDF↔gambar, teks/gambar/anotasi/tanda tangan gambar, proteksi & buka
> proteksi), dan QR Toolkit (generate, desain & logo, ekspor PNG/SVG, batch CSV, baca QR) siap dan
> teruji. Modul gambar/utilitas lanjutan menyusul pada fase berikutnya.

## Fitur QR Toolkit

- **Buat QR**: teks/URL/nomor dengan pratinjau asli, ukuran modul, quiet zone, warna `#RRGGBB`
  (kontras rendah diperingatkan), dan ECC L/M/Q/H.
- **Logo opsional**: cantol logo di tengah (peringatan eksplisit bahwa QR berlogo tidak dijamin
  terbaca); ekspor SVG menolak logo dengan pesan jelas.
- **Ekspor PNG & SVG**: file diverifikasi sebelum disimpan; konflik nama tidak pernah menimpa.
- **Batch dari CSV**: UTF-8 ± BOM, pilih kolom isi & nama file (opsional), progress bar, laporan
  sukses/gagal per baris, batas 100.000 baris.
- **Baca QR**: dari PNG/JPEG/WebP/BMP lokal, multi-QR, dengan batas waktu & piksel. Payload hanya
  teks di layar — tautan di dalam QR tidak pernah dibuka otomatis.

## Fitur PDF Toolkit Dasar

- **Info PDF**: metadata, jumlah halaman, ukuran, status enkripsi (baca-saja; tidak mengarang data).
- **Merge**: gabungkan ≥2 PDF, urutan file dapat diatur.
- **Split**: berdasarkan rentang halaman, atau satu halaman per file.
- **Ekstrak**: ambil halaman tunggal/rentang dengan urutan yang dipertahankan.
- **Susun ulang**: ubah urutan halaman (wajib memuat semua halaman).
- **Rotasi**: putar halaman terpilih atau semua sebesar 90°/180°/270°.

## Fitur PDF Toolkit Lanjutan

- **Kompresi**: mode struktur (lossless), gambar (lossy), dan rasterisasi (dengan peringatan eksplisit).
- **PDF → PNG/JPEG**: render per halaman dengan DPI 36–600 dan penamaan halaman otomatis.
- **Gambar → PDF**: ukuran A4/Letter/ukuran gambar, orientasi, penanganan transparansi & EXIF.
- **Tambah teks & gambar**: kotak teks (fallback font Unicode) dan penempatan gambar ber-proporsi.
- **Anotasi**: highlight (hanya bila teks ditemukan), catatan, kotak, garis/panah.
- **Tanda tangan gambar**: penempatan gambar tanda tangan (bukan tanda tangan digital bersertifikat).
- **Proteksi kata sandi**: AES-256/128 dengan izin dokumen; **buka proteksi** hanya dengan
  kata sandi yang diketahui (tidak pernah memecahkan proteksi).

Semua operasi lokal/offline; file sumber tidak diubah; hasil ditulis ke file baru dengan deteksi
konflik nama. PDF terenkripsi ditolak dengan pesan jelas (kata sandi tidak ditebak/di-log).
Kompresi tidak menjamin hasil lebih kecil (persentase penghematan dilaporkan jujur).

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

## Menjalankan

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python -m office_toolkit
```

Menjalankan tes:

```powershell
$env:QT_QPA_PLATFORM="offscreen"
.\.venv\Scripts\python -m pytest
```

Tanpa virtualenv (paket PDF/UI sudah terpasang di Python 3.12): jalankan dengan `PYTHONPATH=src`
dan pastikan dependensi tersedia. Halaman PDF Toolkit diakses melalui sidebar "PDF Toolkit" dan
"PDF Lanjutan"; halaman "QR Toolkit" menyediakan Buat QR, Batch dari CSV, dan Baca QR.
