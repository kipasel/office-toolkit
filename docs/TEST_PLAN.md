# TEST_PLAN.md — Rencana Pengujian Office Toolkit

Versi: 0.5 (Phase 5 — QR Toolkit)
Status: berjalan. Fondasi (Phase 1), PDF Toolkit Dasar (A1–A7), PDF Toolkit Lanjutan (A8–A14),
dan QR Toolkit (C1–C6) sudah diuji otomatis.

## 1. Prinsip

- Fixture **sintetis** (dibuat oleh kode tes), bukan dokumen kantor nyata.
- Tes memeriksa **hasil operasi nyata**, bukan sekadar keberadaan fungsi.
- Tidak menurunkan standar tes demi jumlah tes lulus.
- Setiap tes membuat file di direktori temporer yang dibersihkan setelah tes.

## 2. Perkakas

- `pytest` 9.1.1 (test runner).
- UI diuji memakai `QApplication` offscreen (`QT_QPA_PLATFORM=offscreen`); **`pytest-qt` belum
  terpasang** di environment — tes UI membuat instance `QApplication` secara manual (lihat
  `tests/ui/`). Jangan klaim memakai `qtbot` sebelum terpasang dan dipakai sungguhan.
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
| `sample_pdf` | PDF 5 halaman berlabel (dari `pdf_factory`) |
| `pdf_with_image` | PDF berlabel + gambar raster (`make_pdf_with_image`) |
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

### 5.2 PDF Toolkit Dasar (A1–A7) — TESTED

Fixture sintetis: `tests/fixtures/pdf_factory.py` + fixture di `tests/conftest.py`
(`sample_pdf` 5 halaman berlabel, `encrypted_pdf`, `corrupt_pdf`). Semua dokumen dibuat oleh kode
tes; tidak memakai dokumen pengguna. Verifikasi urutan halaman memakai teks per halaman.

- Info: jumlah halaman & ukuran benar; metadata kosong ditampilkan `None` (bukan error);
  corrupt → `DecodeError`; terenkripsi → status dilaporkan tanpa membaca metadata. **TESTED**
- Merge: urutan & jumlah halaman benar; input < 2 ditolak; input hilang ditolak; input terenkripsi
  ditolak; file sumber tetap utuh; konflik nama → alternatif. **TESTED**
- Split rentang: satu file per rentang; isi sesuai; rentang di luar batas ditolak. **TESTED**
- Split per halaman: jumlah file = jumlah halaman; nama unik; tiap file 1 halaman. **TESTED**
- Extract: halaman tunggal, urutan khusus, duplikat; di luar batas ditolak; sumber tetap utuh. **TESTED**
- Reorder: urutan berubah sesuai permintaan; wajib permutasi penuh; duplikat/kelurangan ditolak. **TESTED**
- Rotate: 90/180/270; halaman terpilih saja / semua; diverifikasi dengan membuka ulang file;
  sudut & halaman tidak valid ditolak. **TESTED**
- Keamanan & integrasi: sumber tak termodifikasi (hash), PDF terenkripsi ditolak tanpa cracking,
  kata sandi tidak bocor ke pesan error, tidak ada file temporer tertinggal setelah gagal,
  nama output ilegal disanitasi, batas ukuran input ditegakkan, integrasi worker `JobManager`. **TESTED**

Perintah yang dijalankan (Windows, tanpa `.venv`):

```powershell
$env:QT_QPA_PLATFORM="offscreen"
py -3.12 -m pytest
```

Hasil terakhir: **81 passed** (22 tes lama Phase 1/Phase 2 + 59 tes baru Phase 3).

### 5.2b PDF Toolkit Lanjutan (A8–A14) — TESTED

Implementasi: `src/office_toolkit/services/pdf/{common,compress,render,from_images,edit,security}.py`
+ UI `advanced_ui.py` (halaman "PDF Lanjutan", 9 tab). Skenario di bawah mengikuti fitur A–I pada
prompt Phase 4; semua dites dengan dokumen sintetis.

- A Kompresi: mode `struktur` mempertahankan teks & jumlah halaman; mode `images` mempertahankan
  teks yang dapat dicari (lossy → peringatan); mode `rasterize` mempertahankan jumlah halaman dengan
  peringatan eksplisit teks/tautan/bookmark/formulir **tidak** dipertahankan; mode/kualitas/DPI tidak
  valid ditolak; sumber tidak berubah; `savings_pct` mengikuti rumus resmi (negatif = hasil lebih besar). **TESTED**
- B Render: PNG/JPEG, semua/rentang halaman, penamaan `<stem>_page_00N`; DPI di luar 36–600 ditolak;
  format tak dikenal ditolak; konflik nama → alternatif (tidak menimpa); halaman di luar rentang & PDF
  terenkripsi ditolak; sumber tak berubah; render per halaman (tidak memuat seluruh dokumen sekaligus). **TESTED**
- C Gambar→PDF: urutan dipertahankan; ukuran A4/Letter/ukuran gambar; orientasi landscape/portrait;
  transparansi di-flatten atas warna latar; orientasi EXIF diterapkan; TIFF/GIF multi-halaman hanya
  memakai frame pertama (peringatan); gambar rusak dilaporkan per-file tanpa membatalkan sisanya;
  semua rusak → `ProcessingError`. **TESTED**
- D Tambah teks: muncul di halaman target & terverifikasi baca ulang; beberapa halaman; koordinat di
  luar halaman/teks kosong ditolak; Unicode → fallback font sistem atau peringatan (tanpa klaim
  pemakaian font). **TESTED**
- E Tambah gambar: rasio aspek dipertahankan; melebar/panjang dibatasi agar tidak keluar halaman
  (peringatan); rentang halaman; gambar tak valid ditolak; sumber PDF & gambar tetap utuh. **TESTED**
- F Anotasi: highlight hanya bila teks ditemukan; teks tidak ditemukan dilaporkan tanpa highlight palsu;
  note (isi tidak bocor ke teks halaman), rect, line/arrow. **TESTED**
- G Tanda tangan gambar: penempatan di halaman tertentu; peringatan eksplisit **BUKAN** tanda tangan
  digital bersertifikat. **TESTED**
- H Proteksi: file terenkripsi nyata (AES-256/128, `needs_pass`); kata sandi benar → dapat dibuka,
  salah → ditolak tanpa bocor ke error; izin dokumen (print/copy) dihormati dan diverifikasi;
  kata sandi kosong/<4 karakter atau algoritma tak dikenal ditolak; kata sandi tidak pernah masuk
  nama file/log. **TESTED**
- I Buka proteksi: hanya dengan kata sandi diketahui; PDF tak terproteksi ditolak; hasil tanpa sandi
  dengan isi terverifikasi setara sumber. Dikenal kendala PyMuPDF 1.28.x (membaca `needs_pass`
  setelah `authenticate` merusak saluran konten) — dihindari dengan probe terpisah. **TESTED**
- Keamanan (A8–A14): sumber tak termodifikasi untuk semua operasi; tidak ada temp tertinggal setelah
  gagal; kata sandi tidak bocor ke log/pesan; batas piksel & DPI ditegakkan; PDF terenkripsi ditolak
  oleh operasi yang tidak menerima sandi. **TESTED**
- Integrasi & UI: worker `JobManager` kompres→render round-trip; kegagalan worker dilaporkan;
  halaman "PDF Lanjutan" punya 9 tab; navigasi utama sampai index 2; `_run` mematikan/menyalakan tombol. **TESTED**

Perintah yang dijalankan (Windows, tanpa `.venv`):

```powershell
$env:QT_QPA_PLATFORM="offscreen"
py -3.12 -m pytest
```

Hasil terakhir: **156 passed, 1 warning** (peringatan = `qt_api` tidak dikenal di `pyproject.toml`,
diabaikan karena pytest-qt tidak digunakan).

### 5.2c QR Toolkit (C1–C6) — TESTED

Implementasi: `src/office_toolkit/services/qr/{generator,csv_batch,decoder,ui}.py` + fixture
`tests/fixtures/qr_factory.py`. Semua QR dibuat dan dibaca dengan data sintetis (bukan dokumen
pengguna). Round-trip memakai decoder nyata (OpenCV `QRCodeDetector`), bukan asumsi.

- C1 Generate: teks/URL/nomor dengan Unicode; data kosong ditolak; data terlalu panjang ditolak
  dengan pesan jelas. **TESTED**
- C2 Desain: box_size/border/warna/ECC divalidasi; quiet zone < 0 atau box < 1 ditolak; warna harus
  `#RRGGBB`; kontras WCAG < 3.0 memicu peringatan; ECC invalid ditolak; ECC lebih tinggi → QR lebih
  besar. **TESTED**
- C3 Logo: overlay mengubah piksel; peringatan keterbacaan wajib; missing/bukan-gambar → ditolak;
  fraksi > 30% atau ≤ 0 ditolak; PNG berlogo tetap terbaca pada round-trip decode (ECC H). **TESTED**
- C4 Ekspor: PNG dapat dibuka ulang Pillow & ukuran mengikuti desain & warna diterapkan; SVG valid
  (parse XML, ada path, warna mengikuti); SVG + logo → error eksplisit; konflik nama → alternatif
  (tidak menimpa); tidak ada temp tertinggal. **TESTED**
- C5 Batch CSV: UTF-8 ± BOM; header wajib unik & non-kosong; baris kosong dilewati; sel konten
  kosong → gagal per baris; kolom tidak ada → ditolak; nama opsional → fallback `qr_0001`;
  nama sama → `x_1` (anti-overwrite); karakter ilegal / traversal disanitasi; SVG batch sukses;
  SVG + logo ditolak; progress callback (1..N); batas `max_csv_batch_rows` → `ResourceLimitError`;
  hasil per-baris terdecode benar. **TESTED**
- C6 Baca QR: round-trip; multi-QR; `max_items`; gambar tanpa QR → `found=False`; file rusak →
  `DecodeError`; file hilang → `ValidationError`; payload panjang tidak terpotong; batas piksel →
  `ResourceLimitError`; timeout → `ResourceLimitError`. **TESTED**
- Keamanan (QR): traversal via nama CSV diblokir (berada di dalam folder tujuan); tidak pernah
  menimpa diam-diam (ekspor & batch); sumber CSV/gambar tidak termodifikasi (hash); payload tidak
  pernah masuk log; tidak ada temp tertinggal; batas ukuran input ditegakkan; URL payload hanya
  dikembalikan sebagai teks (tidak dibuka). **TESTED**
- Integrasi & UI: worker `JobManager` generate→decode round-trip & batch→decode semua; kegagalan
  worker dilaporkan; halaman "QR Toolkit" punya 3 tab (Buat QR / Batch CSV / Baca QR); navigasi
  utama sampai index 3; pratinjau QR asli tampil & bersih saat data invalid; ekspor PNG via tombol
  menulis file; tab decode menampilkan payload. **TESTED**

Perintah yang dijalankan (Windows, tanpa `.venv`):

```powershell
$env:QT_QPA_PLATFORM="offscreen"
py -3.12 -m pytest
```

Hasil terakhir: **245 passed, 2 warnings** (warning = `qt_api` tidak dikenal di `pyproject.toml`
dan peringatan sporadic libpyside pada penutupan QApplication).

### 5.2d Image Toolkit (B1/B2/B8) — TESTED
- B1 Konversi: PNG→JPEG menghasilkan mode RGB dan file dapat dibuka ulang; header PNG dideteksi
  lewat decoder nyata (bukan ekstensi). **TESTED**
- B2 Resize: lebar jaga rasio aspek (100×50 → 50×25) dan persentase (100×100 @50% → 50×50). **TESTED**
- B8 Hapus metadata: metadata PNG dihapus saat konversi dengan opsi aktif. **TESTED**
- Info: `get_info` melaporkan dimensi; file tidak ada → `ValidationError`. **TESTED**
- UI: halaman "Image Toolkit" punya 3 tab (Info/Konversi/Resize); navigasi utama sampai index 4;
  dispatch job via worker; tab Info menampilkan dimensi; tab Konversi menulis file. **TESTED**

### 5.3 Gambar — sisa Modul B (belum diimplementasikan)
Fitur berikut masih **NOT IMPLEMENTED** dan ditandai eksplisit; kriteria di bawah berlaku saat
diimplementasikan. B1/B2/B8 sudah diuji di §5.2d.
- Konversi format → file hasil dapat dibuka ulang oleh decoder yang benar. (B1: TESTED)
- Resize → dimensi sesuai (piksel/persentase). (B2: TESTED)
- Transparansi → dipertahankan untuk PNG/WebP.
- EXIF orientation → diterapkan benar.
- Batch → laporan jumlah sukses & gagal akurat.
- Target KB → ukuran aktual ditampilkan; bila tak tercapai, dinyatakan gagal.
- File rusak → tidak membuat aplikasi crash.

### 5.4 QR — sudah diuji di §5.2c (C1–C6, Phase 5)

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
