# SECURITY.md — Keamanan, Privasi, dan Sumber Daya

Versi: 0.5 (Phase 5 — QR Toolkit)

## 1. Model Ancaman Ringkas

Office Toolkit memproses file lokal yang mungkin tidak tepercaya (PDF/gambar/CSV dari sumber
eksternal). Risiko utama:

- File rusak/malicious yang memicu crash (decoder).
- Decompression bomb / gambar besar yang menghabiskan memori.
- Overwrite file pengguna secara tidak sengaja.
- Kebocoran data melalui log atau koneksi jaringan.
- Kebocoran kata sandi PDF melalui log/riwayat.

## 2. Privasi & Jaringan

1. Tidak ada cloud API, akun, upload, analytics, atau telemetry.
2. Tidak membuka URL dari dokumen/QR secara otomatis.
3. Tidak ada pemeriksaan update otomatis.
4. Runtime harus berfungsi penuh setelah jaringan diputus — **diverifikasi**, bukan diasumsikan.
5. Perbedaan build-time (unduh dependensi boleh online) vs runtime (wajib offline) didokumentasikan.

## 3. Validasi File (wajib)

- File tidak ditemukan.
- File kosong (0 byte).
- File rusak (gagal dibuka decoder).
- Ekstensi tidak sesuai isi (deteksi via magic number/decoder, bukan ekstensi saja).
- File tidak dapat dibaca (permission).
- Output tidak dapat ditulis.
- Nama file ilegal / benturan nama (termasuk intra-batch).
- Path tidak valid / traversal.
- Ukuran atau kebutuhan sumber daya melebihi batas.

## 4. Batas Sumber Daya

Lihat `docs/SPECIFICATION.md` bagian 10. Nilai default (dapat dikonfigurasi):
ukuran input 500 MB; `MAX_IMAGE_PIXELS` 100 MP; maksimum 5.000 halaman render PDF;
timeout decode QR 30 detik; maksimum 100.000 baris CSV batch. Nilai ini adalah kebijakan aplikasi,
bukan ketentuan Windows.

## 5. Penulisan Output & Integritas

- OutputManager mendukung penulisan temp di direktori tujuan, sanitasi nama, deteksi konflik & alternatif; tidak menimpa tanpa izin.
- Bila gagal/dibatalkan: hapus temporer; jangan meninggalkan output korup yang tampak berhasil.
- Jangan menimpa file tanpa izin eksplisit.
- Jangan menghapus file input sebagai bagian pemrosesan normal.
- Untuk operasi batch, laporkan sukses/gagal per file.
- Operasi PDF (Phase 3) menulis ke file temporer `.pdf`, membuka ulang untuk memverifikasi jumlah
  halaman, lalu `os.replace` atomik ke nama final. File temporer dibersihkan baik saat sukses
  maupun gagal. Nama output disanitasi dan konflik nama tidak menimpa file yang ada.

## 5a. Penanganan PDF Bermasalah (Phase 3)

- File tidak ada/kosong/rusak/bukan PDF → `ValidationError` atau `DecodeError` yang jelas, bukan
  sukses palsu.
- PDF terenkripsi (perlu kata sandi) → ditolak dengan `PasswordError`. Kata sandi **tidak**
  ditebak, tidak dipecahkan, dan tidak ditulis ke log/pesan/nama file.
- Nomor/rentang halaman divalidasi terhadap jumlah halaman; rentang terbalik atau di luar batas
  ditolak sebelum menulis output.
- Folder tujuan tidak dapat ditulis → error sebelum proses; hasil parsial tidak ditinggalkan.
- Batas ukuran input `max_input_mb` ditegakkan (`ResourceLimitError`).
- Informasi PDF bersifat baca-saja; fitur tidak mengklaim PDF aman hanya karena dapat dibuka.
- Keterbatasan pemeliharaan struktur (bookmark/form/metadata) didokumentasikan, bukan disembunyikan.

## 5b. PDF Lanjutan (Phase 4)

- **DPI render** sebagai kebijakan aplikasi: `pdf_render_dpi_min=36`, `pdf_render_dpi_max=600`
  (nilai konfigurasi). Render per halaman (tidak memuat seluruh halaman sekaligus) dan dibatasi
  `max_pdf_pages_render` (5.000 halaman).
- **Piksel gambar** dibatasi `max_image_pixels` (100 MP) untuk semua operasi yang membaca bitmap
  (tambah gambar, gambar→PDF). Pelanggaran → `ResourceLimitError` (fail-fast), tidak diteruskan
  sebagai "gagal per file".
- **Kompresi**: tidak menjanjikan hasil lebih kecil. `savings_pct` mengikuti rumus resmi
  `(awal-hasil)/awal×100`; hasil lebih besar dilaporkan jujur. Mode `rasterize` menghapus
  teks/tautan/bookmark/formulir dan **wajib** menampilkan peringatan eksplisit sebelum menjalankan.
  Mode `images` bersifat lossy (rekompresi JPEG) dan diberi peringatan.
- **Tanda tangan gambar** hanya gambar: peringatan wajib bahwa itu **bukan** tanda tangan digital
  bersertifikat (tanpa identitas/integritas kriptografis) dan tidak dapat dijamin keasliannya.
- **Proteksi kata sandi** (Fitur H): enkripsi AES-256/AES-128 via PyMuPDF; hasil dibuka ulang
  dengan kata sandi untuk mencek `needs_pass` dan jumlah halaman sebelum rename atomik.
  Kata sandi tidak pernah masuk pesan error, nama file, log, atau riwayat. Izin dokumen
  (print/copy/modify/annotate) bersifat himbauan: penegakannya berbeda antar viewer dan bukan
  kontrol akses. Proteksi ≠ jaminan absolut terhadap semua metode serangan (diberi peringatan).
- **Buka proteksi** (Fitur I): hanya dengan kata sandi yang diketahui; tidak pernah mencoba
  memecah/menyiasati proteksi. PDF tanpa proteksi ditolak (`ValidationError`). Hasil diduplikasi ke
  dokumen baru (rebuild) agar saluran konten benar-benar terdekripsi; konsekuensi: bookmark/
  metadata tidak dijamin dipertahankan (didokumentasikan).
- **Kendala PyMuPDF 1.28.x (dihindari)**: membaca `doc.needs_pass`/`is_encrypted` **setelah**
  `authenticate()` berhasil dapat membuat saluran konten tidak lagi terdekripsi (hasil output
  terbaca kosong). Implementasi menghindari hal ini dengan (1) mensyaratkan sandi sebelum proses
  dan (2) menentukan status proteksi lewat probe terpisah (`_open_probe`) yang tidak diautentikasi.

## 5c. QR Toolkit (Phase 5)

- **Baca QR**: gambar divalidasi Pillow lebih dulu (bukan ekstensi), dibatasi `max_image_pixels`;
  decode berjalan dengan guard `qr_decode_timeout_sec` (deafult 30 dtk) → pelanggaran
  `ResourceLimitError` (fail-fast). Payload hasil decode hanya teks di layar: **tidak pernah
  di-log, tidak dibuka sebagai URL, dan tidak dieksekusi**.
- **Generate & ekspor**: PNG/SVG ditulis ke file temporer, diverifikasi (Pillow reopen / XML
  parse) sebelum `os.replace` atomik; temporer dibersihkan saat sukses/gagal. Nama disanitasi
  (karakter ilegal Windows), traversal dicegah, konflik nama memakai alternatif (`x_1.png`) —
  tidak pernah menimpa diam-diam.
- **Logo**: menutupi modul QR → peringatan wajib bahwa QR berlogo **TIDAK dijamin** terbaca;
  fraksi dibatasi `MAX_LOGO_FRACTION` (30%). Ekspor SVG **menolak logo** (error eksplisit).
- **Batch CSV**: header wajib unik & non-kosong; sel konten kosong pada baris terisi dicatat
  gagal per baris (baris fisik 1-based); baris sepenuhnya kosong dilewati; cache file/folder
  tujuan divalidasi; sumber CSV tidak pernah dimodifikasi.
- **Kontras warna**: fg/bg harus `#RRGGBB`; rasio WCAG < 3.0 memicu peringatan keterbacaan.

## 6. Kata Sandi & Rahasia

- Kata sandi PDF tidak ditulis ke log, riwayat, atau nama file.
- Kata sandi tidak disimpan di konfigurasi.
- Log merahkan path sensitif bila perlu.

## 7. Logging

- Log lokal dengan rotasi.
- Tidak memuat isi dokumen, kata sandi, atau data sensitif.
- Error dicatat dengan konteks (operasi, tipe error), bukan isi file.

## 8. Operasi Berisiko & Peringatan

- Rendering ulang PDF berpotensi menurunkan kualitas / menghilangkan elemen interaktif → peringatan.
- Bookmark/metadata/tautan/formulir/tanda tangan digital dipertahankan bila didukung; bila operasi
  berpotensi menghilangkannya → peringatan sebelum proses.
- Tanda tangan digital kriptografis tidak dijamin valid setelah modifikasi; bedakan dari gambar
  tanda tangan.
- Operasi massal memerlukan konfirmasi.

## 9. Lisensi Dependensi (perlu keputusan)

| Paket | Lisensi | Implikasi |
|---|---|---|
| PyMuPDF | **AGPL-3.0** (atau komersial) | Distribusi AGPL atau beli lisensi komersial. **Perlu keputusan pengguna.** |
| PySide6 / Qt | LGPLv3 (opsi komersial) | Ikuti kewajiban LGPL (dynamic linking, atribusi). |
| pypdf | BSD-3-Clause | Sertakan notice. |
| Pillow | MIT-CMU | Sertakan notice. |
| qrcode | BSD-2-Clause | Sertakan notice. |
| opencv-python-headless | Apache-2.0 | Sertakan notice. Pengganti zxing-cpp (diblokir Smart App Control; lihat SPECIFICATION §12). |
| numpy | BSD-3-Clause | Sertakan notice. Dependensi opencv-headless. |
| pytest / pytest-qt | MIT | Dev-only, tidak didistribusikan. |
| PyInstaller | GPL-2.0 + bootloader exception | Boleh packaging aplikasi non-GPL. |

Audit lisensi penuh dilakukan pada Phase 5 sebelum distribusi. Pemberitahuan lisensi disertakan
dalam build.
