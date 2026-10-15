# FEATURE_MATRIX.md — Matriks Fitur & Status

Status: 0.6 (Phase 5 — QR Toolkit + Image Toolkit B1/B2/B8)
Legenda status: **NOT IMPLEMENTED** · **IMPLEMENTED** · **TESTED** · **VERIFIED** · **BLOCKED**
Legenda tes: `—` belum ada.

> Catatan penomoran: dokumen ini awalnya memberi label "Phase 2" untuk Modul A. Prompt induk
> menyebut PDF Toolkit Dasar sebagai **Phase 3**, PDF Toolkit Lanjutan sebagai **Phase 4**, dan
> QR Toolkit sebagai **Phase 5**.
> Status `TESTED` berarti tes otomatis sudah dijalankan dan lulus; belum `VERIFIED`
> karena belum ada penerimaan/verifikasi manual pada dokumen nyata pengguna.

## Fondasi (Phase 1)

| ID | Fitur | Status | Tes | Catatan |
|---|---|---|---|---|
| F1 | Konfigurasi proyek (pyproject, requirements) | IMPLEMENTED | TESTED | Phase 1 — 15 unit+UI tests lulus |
| F2 | Entry point & bootstrap | IMPLEMENTED | TESTED | Phase 1 |
| F3 | Logging lokal + redaksi | IMPLEMENTED | TESTED | Phase 1 |
| F4 | Hierarki error | IMPLEMENTED | TESTED | Phase 1 |
| F5 | Validasi file | IMPLEMENTED | TESTED | Phase 1; dipakai ulang oleh PDF Toolkit |
| F6 | Output manager | IMPLEMENTED | TESTED | Phase 1; dipakai ulang oleh PDF Toolkit |
| F7 | Job manager + worker Qt | IMPLEMENTED | TESTED | Phase 1; dipakai ulang oleh PDF Toolkit |
| F8 | Main window + navigasi + dashboard | IMPLEMENTED | TESTED | Phase 1; navigasi menuju halaman PDF ditambahkan (Phase 3) |
| F9 | Komponen UI dasar | IMPLEMENTED | TESTED | FileSelector, FolderSelector, PlaceholderPage, Theme |

## Modul A — PDF Toolkit Dasar (Phase 3)

Implementasi: `src/office_toolkit/services/pdf/{processor,ui}.py`. Semua operasi memakai
PyMuPDF (satu library, sesuai keputusan arsitektur), berjalan lokal/offline, dan menulis hasil
lewat `OutputManager` (file temporer + `os.replace` atomik, verifikasi jumlah halaman sebelum
rename).

| ID | Fitur | Status | Tes | Catatan |
|---|---|---|---|---|
| A1 | Info PDF (metadata, halaman, ukuran) | IMPLEMENTED | TESTED | 6 tes; PDF terenkripsi dilaporkan statusnya, metadata tidak dikarang |
| A2 | Merge PDF (urutan dapat diubah) | IMPLEMENTED | TESTED | 6 tes; urutan via daftar UI; konflik nama dibuat alternatif |
| A3 | Split berdasarkan rentang | IMPLEMENTED | TESTED | Rentang 1-based; tumpang tindih diizinkan (satu file per rentang) |
| A4 | Split per halaman | IMPLEMENTED | TESTED | Nama file menyertakan nomor halaman ber-zero-pad, anti-tabrakan |
| A5 | Extract halaman | IMPLEMENTED | TESTED | Mendukung halaman tunggal, rentang, duplikat; urutan dipertahankan |
| A6 | Reorder halaman | IMPLEMENTED | TESTED | Wajib permutasi penuh 1..N (tidak ada halaman hilang) |
| A7 | Rotate halaman | IMPLEMENTED | TESTED | 90/180/270; halaman terpilih atau semua; diverifikasi baca ulang |
| A8 | Kompresi PDF (3 mode) | IMPLEMENTED | TESTED | struktur (lossless), images (lossy `rewrite_images`), rasterize (peringatan eksplisit) |
| A9 | Tambah teks & gambar | IMPLEMENTED | TESTED | kembali teks via kotak teks (fallback font Unicode), gambar via koordinat+lebar |
| A10 | Anotasi dasar | IMPLEMENTED | TESTED | highlight (wajib ditemukan), note, rect, line/arrow; tanpa highlight palsu |
| A11 | Tanda tangan gambar + pratinjau | IMPLEMENTED | TESTED | penempatan gambar; peringatan eksplisit BUKAN tanda tangan digital |
| A12 | PDF → PNG/JPEG (DPI) | IMPLEMENTED | TESTED | per halaman `<stem>_page_00N.{png,jpg}`; batas DPI 36–600 |
| A13 | Gambar → PDF | IMPLEMENTED | TESTED | A4/Letter/ukuran gambar; orientasi; transparansi; EXIF; frame-1 TIFF |
| A14 | Proteksi & buka proteksi kata sandi | IMPLEMENTED | TESTED | AES-256/128, izin dokumen; buka proteksi hanya dengan kata sandi diketahui |

### Keterbatasan yang terdokumentasi (Phase 3)

- Merge/split/extract/reorder membentuk dokumen baru via `insert_pdf`; **bookmark/outline, XMP
  metadata, dan sebagian struktur formulir tidak dijamin dipertahankan** (lihat juga SPECIFICATION §5).
  Rotate memodifikasi salinan dokumen sehingga metadata/outline cenderung tetap.
- PDF terenkripsi **ditolak** (`PasswordError`); kata sandi tidak pernah ditebak/dipecahkan/di-log.
- Ukuran input dibatasi `AppConfig.max_input_mb` (default 500 MB).

### Keterbatasan yang terdokumentasi (Phase 4)

- Kompresi tidak menjamin hasil lebih kecil; `savings_pct` negatif berarti hasil lebih besar (dilaporkan,
  bukan disembunyikan). Mode `rasterize` mengubah tiap halaman menjadi gambar: teks/tautan/bookmark/isi
  formulir **tidak dipertahankan** (peringatan eksplisit wajib ditampilkan sebelum menjalankan).
- Mode `images` (rekompresi JPEG) bersifat lossy; kualitas visual dapat menurun.
- Tanda tangan gambar **bukan** tanda tangan digital tersertifikasi (tanpa identitas/integritas kriptografis).
- `decrypt` menduplikasi halaman ke dokumen baru (rebuild); bookmark/metadata tidak dijamin dipertahankan.
  Dikenal kendala PyMuPDF 1.28.x: membaca `doc.needs_pass` *setelah* `authenticate()` merusak saluran
  konten — dihindari dengan probe terpisah (lihat `SECURITY.md` §Proteksi).
- Proteksi kata sandi ≠ jaminan absolut; izin dokumen bersifat himbauan, penegakannya bergantung viewer.


## Modul B — Image Toolkit

Implementasi: `src/office_toolkit/services/images/{processor,ui}.py`. Operasi memakai Pillow,
berjalan lokal/offline, dan menulis hasil lewat `OutputManager` (anti-overwrite). Halaman
"Image Toolkit" menyediakan tiga tab nyata: **Info**, **Konversi**, dan **Resize**. Sisa
sub-fitur Modul B (compress khusus, target KB, crop, rotate, batch, orientasi EXIF) belum dibuat.

| ID | Fitur | Status | Tes | Catatan |
|---|---|---|---|---|
| B1 | Konversi format | IMPLEMENTED | TESTED | PNG/JPEG/WebP/BMP/TIFF; transparansi di-flatten ke putih saat JPEG |
| B2 | Resize (piksel/persentase) | IMPLEMENTED | TESTED | lebar jaga rasio aspek atau persentase; LANCZOS |
| B3 | Compress (kualitas) | NOT IMPLEMENTED | — | kontrol kualitas ada di tab Konversi (JPEG/WebP), belum alat compress tersendiri |
| B4 | Target ukuran file (KB) | NOT IMPLEMENTED | — | |
| B5 | Crop manual | NOT IMPLEMENTED | — | |
| B6 | Rotate | NOT IMPLEMENTED | — | |
| B7 | Batch convert & resize | NOT IMPLEMENTED | — | |
| B8 | Hapus metadata | IMPLEMENTED | TESTED | opsi "Hapus metadata (EXIF)" pada tab Konversi (PNG/JPEG/WebP/TIFF) |
| B9 | Pratinjau & ukuran sebelum/sesudah | NOT IMPLEMENTED | — | ukuran sebelum/sesudah dilaporkan, pratinjau visual belum ada |
| B10 | Penanganan transparansi | NOT IMPLEMENTED | — | transparansi dipertahankan untuk PNG/WebP; belum alat khusus |
| B11 | Orientasi EXIF | NOT IMPLEMENTED | — | |

## Modul C — QR Code (Phase 5)

Implementasi: `src/office_toolkit/services/qr/{generator,csv_batch,decoder,ui}.py`. Generate
memakai `qrcode` (PNG/SVG), baca memakai OpenCV `QRCodeDetector` (opencv-python-headless) —
pengganti zxing-cpp yang diblokir Smart App Control (lihat `SPECIFICATION.md` §3.3/§12).
Semua operasi offline; payload tidak pernah di-log; tautan tidak dibuka otomatis.

| ID | Fitur | Status | Tes | Catatan |
|---|---|---|---|---|
| C1 | Generate QR (teks/URL/nomor) | IMPLEMENTED | TESTED | QrToolkitPage » tab "Buat QR"; pratinjau asli dari input |
| C2 | Pengaturan ukuran/margin/warna/ECC | IMPLEMENTED | TESTED | box_size, quiet zone, #RRGGBB, ECC L/M/Q/H; kontras ≤ 3.0 diperingatkan |
| C3 | Logo opsional + peringatan | IMPLEMENTED | TESTED | fraksi logo ≤ 30%; peringatan TIDAK dijamin terbaca; ditolak untuk SVG |
| C4 | Ekspor PNG & SVG | IMPLEMENTED | TESTED | verifikasi buka-ulang/parse sebelum rename atomik |
| C5 | Generate massal dari CSV | IMPLEMENTED | TESTED | UTF-8±BOM; kolom isi + nama opsional; progress; kegagalan per baris |
| C6 | Baca QR dari gambar lokal | IMPLEMENTED | TESTED | multi-QR; timeout & batas piksel; payload teks, tanpa membuka URL |

### Keterbatasan yang terdokumentasi (Phase 5)

- QR berlogo **TIDAK dijamin** tetap dapat dipindai; risiko meningkat seiring ukuran logo.
- Ekspor **SVG tidak mendukung logo** (error eksplisit, bukan drop diam-diam).
- Batas data QR bergantung versi + konten + ECC; data terlalu panjang ditolak dengan pesan jelas.
- Decoder berbasis OpenCV `QRCodeDetector`: cukup cepat & akurat untuk dokumen umum, tetapi barcode
  1D dan sebagian varian QR kustom tidak didukung; tiap gambar dibatasi waktu
  (`qr_decode_timeout_sec`, default 30 dtk) dan piksel (`max_image_pixels`).
- CSV dihitung per baris fisik; sel kosong pada baris terisi → dicatat gagal (bukan dilewati).
  Baris yang sepenuhnya kosong dilewati.

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
