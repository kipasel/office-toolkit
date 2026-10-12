# SECURITY.md — Keamanan, Privasi, dan Sumber Daya

Versi: 0.1 (Phase 0)

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
| zxing-cpp | Apache-2.0 | Sertakan notice. |
| pytest / pytest-qt | MIT | Dev-only, tidak didistribusikan. |
| PyInstaller | GPL-2.0 + bootloader exception | Boleh packaging aplikasi non-GPL. |

Audit lisensi penuh dilakukan pada Phase 5 sebelum distribusi. Pemberitahuan lisensi disertakan
dalam build.
