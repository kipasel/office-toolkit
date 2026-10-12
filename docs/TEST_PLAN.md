# TEST_PLAN.md — Rencana Pengujian Office Toolkit

Versi: 0.1 (Phase 0)
Status: rencana. Belum ada tes yang dijalankan.

## 1. Prinsip

- Fixture **sintetis** (dibuat oleh kode tes), bukan dokumen kantor nyata.
- Tes memeriksa **hasil operasi nyata**, bukan sekadar keberadaan fungsi.
- Tidak menurunkan standar tes demi jumlah tes lulus.
- Setiap tes membuat file di direktori temporer yang dibersihkan setelah tes.

## 2. Perkakas

- `pytest` 9.1.1 (test runner).
- `pytest-qt` 4.5.0 (pengujian UI Qt; gunakan `qtbot`, mode `offscreen`).
- Fixture pembuat PDF/gambar/QR sintetis (modul `tests/fixtures/`).

## 3. Konfigurasi & Perintah

```powershell
# semua tes
.\.venv\Scripts\python -m pytest

# per kategori
.\.venv\Scripts\python -m pytest tests/unit
.\.venv\Scripts\python -m pytest tests/integration
.\.venv\Scripts\python -m pytest tests/ui
.\.venv\Scripts\python -m pytest tests/security
```

UI test dijalankan dengan `QT_QPA_PLATFORM=offscreen` pada CI/headless.

## 4. Fixture Sintetis yang Dibutuhkan

| Fixture | Isi |
|---|---|
| `sample_pdf_n` | PDF N halaman (ukuran halaman diketahui) |
| `encrypted_pdf` | PDF terenkripsi dengan kata sandi diketahui |
| `corrupt_pdf` | File dengan header PDF rusak |
| `sample_images` | PNG transparan, JPEG EXIF-orientation, TIFF multi-halaman, WebP, BMP |
| `corrupt_image` | File gambar rusak |
| `qr_expected` | Teks/URL/nomor untuk round-trip QR |
| `csv_batch` | CSV untuk generate massal (termasuk baris kosong, encoding UTF-8) |
| `duplicate_files` | Beberapa file identik untuk uji SHA-256 |

## 5. Tes per Modul

### 5.1 Fondasi (Phase 1) — VERIFIED
- Aplikasi start tanpa error (smoke). **TESTED**
- Navigasi dasar (sidebar) berfungsi. **TESTED**
- Worker: lifecycle job (queued/running/succeeded/failed/cancelled) via signals, UI tidak diblokir. **TESTED**
- Output manager: nama aman, deteksi konflik + alternatif, bersihkan temporer, tidak menimpa tanpa izin. **TESTED**
- Logging: konfigurasi lokal, rotasi, tidak memuat isi dokumen/kata sandi. **TESTED**
- Validasi file: file tidak ada, kosong, path ilegal, baca/tulis aman. **TESTED**

### 5.2 PDF (Phase 2)
- Merge 2 PDF → jumlah halaman = total, urutan sesuai input.
- Split rentang → halaman sesuai; rentang di luar batas ditolak dengan pesan jelas.
- Extract & reorder → urutan halaman benar.
- Rotate → orientasi halaman terpilih berubah, lainnya tetap.
- Compress → PDF dapat dibuka; ukuran awal & akhir dilaporkan; bila tidak mengecil, dilaporkan.
- PDF→gambar → dimensi sesuai pengaturan DPI.
- Gambar→PDF → jumlah halaman benar.
- PDF terenkripsi → meminta kata sandi bila perlu; kata sandi salah ditolak jelas.
- File rusak → error jelas, bukan sukses palsu.

### 5.3 Gambar (Phase 3)
- Konversi format → file hasil dapat dibuka ulang oleh decoder yang benar.
- Resize → dimensi sesuai (piksel/persentase).
- Transparansi → dipertahankan untuk PNG/WebP.
- EXIF orientation → diterapkan benar.
- Batch → laporan jumlah sukses & gagal akurat.
- Target KB → ukuran aktual ditampilkan; bila tak tercapai, dinyatakan gagal.
- File rusak → tidak membuat aplikasi crash.

### 5.4 QR (Phase 4)
- Round-trip: generate → decode (zxing-cpp) → nilai sama dengan input.
- PNG & SVG dapat dibuka pembaca yang sesuai.
- CSV batch → jumlah output = jumlah baris valid; baris kosong diabaikan sesuai aturan.
- Input kosong/invalid ditangani benar.
- Logo opsional tidak merusak alur tanpa peringatan.
- Decoder tidak dijalankan otomatis membuka URL.

### 5.5 File Utilities (Phase 4)
- Rename preview sesuai harapan.
- Benturan nama terdeteksi sebelum eksekusi (termasuk benturan intra-batch).
- Duplikat teridentifikasi via hash.
- CSV & JSON output valid; JSON divalidasi sebelum format.
- Tidak ada file yang ditimpa diam-diam.

### 5.6 UI & Integrasi
- Aplikasi start tanpa error.
- Navigasi semua halaman berfungsi.
- Operasi berat tidak membekukan UI.
- Error ditampilkan benar.
- Pembatalan & pembersihan temporer diuji pada operasi yang mendukung.
- Pengaturan output konsisten.
- Setiap fitur berstatus VERIFIED harus punya tes relevan.

### 5.7 Security (Phase 5)
- Tidak ada koneksi jaringan saat runtime (verifikasi, bukan asumsi).
- Tidak ada pembukaan URL otomatis dari QR/dokumen.
- Log tidak memuat isi dokumen/kata sandi.
- Batas sumber daya mencegah OOM/decompression bomb.
- File input tidak terhapus setelah pemrosesan.

### 5.8 Distribusi (Phase 5)
- Build berhasil dibuat di Windows.
- Jalankan executable hasil build (bukan entry point Python).
- Uji startup + PDF + gambar + QR pada build.
- Uji runtime tanpa koneksi internet.
- Periksa resource/ikon/font/dependensi ikut terkemas; catat ukuran build aktual.
- Bila build tidak dapat dijalankan di environment tersedia → **BLOCKED**.

## 6. Pelaporan

Setiap hasil phase melaporkan perintah yang benar-benar dijalankan, jumlah tes lulus/gagal, error/
warning penting, dan status tiap fitur (IMPLEMENTED/TESTED/VERIFIED/BLOCKED/NOT IMPLEMENTED).
