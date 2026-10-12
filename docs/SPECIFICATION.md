# SPECIFICATION.md — Spesifikasi Teknis Office Toolkit

Versi dokumen: 0.1 (Phase 0)
Status: menunggu persetujuan pengguna.

Dokumen ini adalah **sumber kebenaran** untuk ruang lingkup dan perilaku teknis. Bila ada
pertentangan dengan dokumen lain, dokumen ini menang.

## 1. Tujuan dan Prinsip

Aplikasi desktop Windows untuk mengolah PDF, gambar, QR Code, dan utilitas file kantor secara
lokal. Prinsip prioritas:

1. Kebenaran hasil pemrosesan.
2. Privasi dan keamanan file.
3. Stabilitas aplikasi.
4. Pengujian yang dapat diulang.
5. UI profesional.
6. Distribusi Windows yang dapat diverifikasi.

## 2. Platform

- Windows 10/11 64-bit (x64). Environment audit: Windows 11 (10.0.26200), AMD64.
- Python **3.12**. Interpreter target: `py -3.12`.
- GUI: PySide6 (Qt 6).

## 3. Dependensi (diusulkan, menunggu persetujuan)

Semua versi di bawah **diverifikasi dapat diunduh/di-resolve** untuk CPython 3.12 win_amd64 pada
index yang tersedia di environment audit. Nomor versi diambil dari metadata paket, bukan dikarang.

### 3.1 Runtime

| Paket | Versi | Peran | Ukuran wheel (win_amd64) | Lisensi |
|---|---|---|---|---|
| PySide6 | 6.11.2 | UI desktop | (terpasang) | LGPLv3 / komersial Qt |
| pymupdf | 1.28.2 | Rendering, manipulasi PDF/gambar | (terpasang) | AGPL-3.0 / komersial |
| pypdf | 6.20.0 | Operasi struktural PDF (merge/split/encrypt ringan) | 402 KB | BSD-3-Clause |
| pillow | 11.3.0 | Pengolahan gambar | (terpasang) | MIT-CMU |
| qrcode | 8.2 | Generate QR (PNG/SVG) | 46 KB | BSD-2-Clause |
| zxing-cpp | 3.1.1 | Baca/decode QR Code | 1.0 MB | Apache-2.0 |
| pikepdf | 9.11.0 | Enkripsi/buka proteksi PDF | (terpasang) | MPL-2.0 |

### 3.2 Development

| Paket | Versi | Peran | Lisensi |
|---|---|---|---|
| pytest | 9.1.1 | Test runner | MIT |
| pytest-qt | 4.5.0 | Pengujian UI Qt | MIT |
| pyinstaller | 6.21.0 | Build Windows | GPL-2.0 dengan pengecualian bootloader |

### 3.3 Keputusan dependensi yang perlu konfirmasi

1. **QR decoder: `zxing-cpp` (1 MB) vs `opencv-python-headless` (39,4 MB + numpy ~15 MB).**
   Rekomendasi: **zxing-cpp** — wheel cp312 tersedia, decoder murni QR/barcode tanpa menarik
   numpy, jauh lebih kecil untuk packaging. OpenCV hanya dipertimbangkan bila zxing terbukti gagal
   menangani kasus yang disyaratkan. Spec mengizinkan "OpenCV atau library lokal yang sesuai".
2. **`pikepdf` 9.11.0 (terpasang, MPL-2.0)** — kandidat untuk enkripsi/dekripsi PDF yang lebih
   tahan banting. Belum dimasukkan ke daftar terkunci. Perlu keputusan bila PyMuPDF/pypdf kurang
   andal untuk kasus enkripsi.
3. **`numpy`** — saat ini tidak diperlukan bila memilih zxing-cpp.

Catatan lisensi: `pymupdf` berlisensi **AGPL-3.0**. Ini memengaruhi distribusi. Perlu keputusan
pengguna (lihat bagian 12 dan `docs/SECURITY.md`).

## 4. Ketentuan Offline dan Privasi (wajib)

1. Tidak ada cloud API, upload file, akun, atau layanan eksternal.
2. Tidak ada analytics/telemetry/crash-report jaringan.
3. Tidak mengirim nama file, isi, metadata, atau info pengguna ke internet.
4. Tidak membuka URL dari dokumen/QR secara otomatis.
5. Tidak ada pemeriksaan update otomatis.
6. Font, ikon, stylesheet, resource UI lokal.
7. Runtime harus berfungsi setelah koneksi jaringan diputus; status offline **diverifikasi**,
   bukan disimpulkan dari ketiadaan kode API.
8. Proses build/unduh dependensi memerlukan internet; runtime tidak.
9. File sumber tidak dihapus otomatis.
10. Log tidak memuat isi dokumen, kata sandi, atau data sensitif; path sensitif diredaksi.

## 5. Modul A — PDF Toolkit

| # | Fitur | Perilaku yang disyaratkan |
|---|---|---|
| A1 | Info PDF | Tampilkan metadata, jumlah halaman, ukuran file |
| A2 | Merge | Gabung ≥2 PDF, urutan dapat diubah pengguna |
| A3 | Split (rentang) | Pisah berdasarkan rentang halaman tervalidasi |
| A4 | Split per halaman | Satu file per halaman |
| A5 | Extract halaman | Ambil halaman terpilih |
| A6 | Reorder halaman | Susun ulang urutan halaman |
| A7 | Rotate halaman | Putar halaman terpilih (0/90/180/270) |
| A8 | Tambah teks & gambar | Sisipkan pada posisi halaman |
| A9 | Anotasi dasar | Highlight/underline/note (sesuai dukungan PyMuPDF) |
| A10 | Tanda tangan gambar | Sisipkan gambar tanda tangan + pratinjau posisi/ukuran |
| A11 | PDF → PNG/JPEG | Render per halaman, atur resolusi (DPI) |
| A12 | Gambar → PDF | Satu/lebih gambar menjadi PDF |
| A13 | Proteksi kata sandi | Enkripsi PDF dengan kata sandi |
| A14 | Buka proteksi | Hanya bila kata sandi diketahui & pengguna berwenang |
| A15 | Metadata | (bagian dari A1) |

Ketentuan PDF:

- Validasi rentang halaman, nomor halaman, ukuran file, keberadaan file.
- Kompresi tidak dijamin memperkecil. Laporkan ukuran awal & akhir apa adanya; bila tidak mengecil,
  nyatakan dengan jelas.
- Tidak menjanjikan editing teks penuh seperti Word.
- Tidak mengklaim dapat memecahkan kata sandi yang tidak diketahui.
- Pertahankan urutan halaman & orientasi sesuai instruksi.
- Operasi rendering ulang berpotensi menurunkan kualitas / menghilangkan elemen interaktif —
  beri peringatan.
- Bookmark/metadata/tautan/formulir/tanda tangan digital dipertahankan bila didukung; jika operasi
  berpotensi menghilangkannya, beri peringatan sebelum proses.
- Tanda tangan digital kriptografis **tidak** dijamin valid setelah modifikasi. Bedakan dari gambar
  tanda tangan.

## 6. Modul B — Image Toolkit

Format: JPEG/JPG, PNG, WebP, BMP, TIFF.

| # | Fitur | Perilaku yang disyaratkan |
|---|---|---|
| B1 | Konversi format | Dekode dengan decoder nyata, lalu encode ke format target |
| B2 | Resize | Piksel atau persentase |
| B3 | Compress | Pengaturan kualitas |
| B4 | Target ukuran (KB) | Percobaan terkontrol; laporkan ukuran aktual; bila gagal, nyatakan gagal |
| B5 | Crop manual | Area crop dari UI |
| B6 | Rotate | 90/180/270, sesuai EXIF |
| B7 | Batch convert/resize | Laporkan sukses/gagal per file |
| B8 | Hapus metadata | Opsional |
| B9 | Pratinjau & ukuran sebelum/sesudah | Nyata dari file |
| B10 | Transparansi | Dipertahankan bila format mendukung |

Ketentuan: jangan ubah file asli tanpa persetujuan; pertahankan transparansi; tangani EXIF
orientation; jangan buang frame animasi/halaman TIFF tanpa pemberitahuan; hindari memori berlebih
untuk gambar besar; validasi via decoder, bukan ekstensi.

## 7. Modul C — QR Code

| # | Fitur | Perilaku yang disyaratkan |
|---|---|---|
| C1 | Generate QR | Dari teks/URL/nomor |
| C2 | Pengaturan | Ukuran, margin, warna, error correction |
| C3 | Logo opsional | Dengan peringatan keterbacaan |
| C4 | Ekspor PNG & SVG | File dapat dibuka pembaca yang sesuai |
| C5 | Generate massal dari CSV | Nama file aman, hindari konflik |
| C6 | Baca QR dari gambar lokal | Hasil decode = isi asli |

Ketentuan: validasi input; preview = QR yang benar-benar dihasilkan; jangan membuka URL otomatis;
QR tidak diklaim dapat dipindai sebelum decode otomatis/verifikasi berhasil; CSV menangani encoding
dan baris kosong secara eksplisit. Barcode 1D **tidak** termasuk.

## 8. Modul D — File Utilities

| # | Fitur | Perilaku yang disyaratkan |
|---|---|---|
| D1 | Batch rename | Awalan, akhiran, pola nama, nomor urut |
| D2 | Pratinjau rename | Nama lama → nama baru |
| D3 | Deteksi duplikat | Berdasarkan SHA-256 |
| D4 | Ekspor daftar file | Ke CSV |
| D5 | Format TXT/CSV/JSON | Aturan eksplisit; JSON divalidasi sebelum diformat |
| D6 | Foto dokumen | Crop, rotate, tingkatkan kontras |
| D7 | Ekspor foto dokumen → PDF | — |
| D8 | Pilih folder output | — |
| D9 | Riwayat operasi lokal | Dapat dihapus pengguna |

Ketentuan: cek benturan nama termasuk antarfile dalam satu batch; tidak menimpa file diam-diam;
konfirmasi sebelum operasi massal; CSV aman untuk teks/encoding; jangan menyebut pemformatan teks
sebagai konversi dokumen yang mempertahankan seluruh struktur.

## 9. Standar UI/UX

- PySide6; tema terang default; dasar putih/abu netral + aksen biru tua.
- Sidebar navigasi; dashboard dengan pencarian & kategori; workspace per fitur.
- Drag-and-drop bila relevan; tombol pilih file/folder selalu tersedia.
- Pratinjau hasil; progress nyata (busy indicator bila tanpa persentase).
- Pesan sukses/gagal jelas; tombol buka folder output.
- Bahasa Indonesia; layout adaptif saat ukuran jendela berubah.
- Operasi lama di worker Qt; akses widget hanya via signal/slot (thread-safe).
- Tidak ada tombol tanpa aksi; tombol fitur belum tersedia dinonaktifkan eksplisit.

## 10. Batas Sumber Daya (usulan, dapat dikonfigurasi)

Nilai ini adalah **kebijakan aplikasi**, bukan ketentuan Windows. Dapat diubah di `core/config.py`.

| Parameter | Nilai awal | Alasan |
|---|---|---|
| Ukuran maksimum 1 file input PDF/gambar | 500 MB | Cegah OOM & waktu proses ekstrem |
| Batas `Pillow.MAX_IMAGE_PIXELS` | 100.000.000 px | Cegah decompression bomb |
| Jumlah halaman maksimum render PDF | 5.000 | Cegah konsumsi memori/disk berlebih |
| Timeout decode QR per gambar | 30 detik | Cegah hang |
| Ukuran maksimum CSV batch QR | 100.000 baris | Batas wajar operasi massal |

Bila input melebihi batas, tolak dengan pesan jelas (bukan crash).

## 11. Distribusi

- PyInstaller (`app.spec`), target onedir sebagai default (lebih stabil untuk Qt).
- Uji build di Windows: jalankan **executable hasil build**, bukan hanya entry point Python.
- Uji startup, PDF, gambar, QR pada build; uji runtime tanpa internet.
- Periksa resource/ikon/font/dependensi ikut terkemas; catat ukuran build aktual.
- Bila build tidak dapat dijalankan di environment yang tersedia, tandai **BLOCKED**, bukan
  VERIFIED.

## 12. Pertanyaan yang Menghambat (butuh keputusan pengguna)

Lihat juga akhir laporan Phase 0. Ringkasan:

1. QR decoder: **zxing-cpp** (disetujui).
2. Lisensi PyMuPDF (AGPL-3.0): **Terima AGPL – aplikasi akan dipublikasikan sesuai AGPL-3.0**.
3. `pikepdf` (9.11.0, MPL-2.0): **ditambahkan** untuk enkripsi/buka proteksi PDF.
4. Target distribusi: **onedir** (disetujui).
5. Batas sumber daya bagian 10: **disetujui** (dapat dikonfigurasi).
