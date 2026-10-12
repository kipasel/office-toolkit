# FEATURE_MATRIX.md — Matriks Fitur & Status

Status: 0.3 (Phase 3 — PDF Toolkit Dasar)
Legenda status: **NOT IMPLEMENTED** · **IMPLEMENTED** · **TESTED** · **VERIFIED** · **BLOCKED**
Legenda tes: `—` belum ada.

> Catatan penomoran: dokumen ini awalnya memberi label "Phase 2" untuk Modul A. Prompt induk
> menyebut PDF Toolkit Dasar sebagai **Phase 3**. Keduanya merujuk pada kumpulan fitur A1–A7 di
> bawah. Status `TESTED` berarti tes otomatis sudah dijalankan dan lulus; belum `VERIFIED`
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
| A8 | Tambah teks & gambar | NOT IMPLEMENTED | — | Di luar scope Phase 3 |
| A9 | Anotasi dasar | NOT IMPLEMENTED | — | Di luar scope Phase 3 |
| A10 | Tanda tangan gambar + pratinjau | NOT IMPLEMENTED | — | Di luar scope Phase 3 |
| A11 | PDF → PNG/JPEG (DPI) | NOT IMPLEMENTED | — | Di luar scope Phase 3 |
| A12 | Gambar → PDF | NOT IMPLEMENTED | — | Di luar scope Phase 3 |
| A13 | Proteksi kata sandi | NOT IMPLEMENTED | — | Di luar scope Phase 3 |
| A14 | Buka proteksi (kata sandi diketahui) | NOT IMPLEMENTED | — | Di luar scope Phase 3 |

### Keterbatasan yang terdokumentasi (Phase 3)

- Merge/split/extract/reorder membentuk dokumen baru via `insert_pdf`; **bookmark/outline, XMP
  metadata, dan sebagian struktur formulir tidak dijamin dipertahankan** (lihat juga SPECIFICATION §5).
  Rotate memodifikasi salinan dokumen sehingga metadata/outline cenderung tetap.
- PDF terenkripsi **ditolak** (`PasswordError`); kata sandi tidak pernah ditebak/dipecahkan/di-log.
- Ukuran input dibatasi `AppConfig.max_input_mb` (default 500 MB).


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
