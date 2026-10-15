# AGENTS.md — Office Toolkit

Dokumen ini adalah panduan operasional untuk agen (manusia atau AI) yang bekerja pada repository ini.
Bacalah dokumen ini lebih dahulu sebelum mengubah apa pun.

## 1. Ringkasan Proyek

**Office Toolkit** adalah aplikasi desktop Windows (offline, privat) untuk mengolah PDF, gambar,
QR Code, dan utilitas file kantor. Fokus utama: hasil pemrosesan yang benar, privasi file, stabilitas,
dan pengujian yang dapat diulang.

Status saat ini: **PHASE 6 (Metro UI Redesign)** — kode aplikasi sudah ada. Fondasi/UI, PDF Toolkit
Dasar (A1–A7), PDF Toolkit Lanjutan (A8–A14), QR Toolkit (C1–C6), dan Image Toolkit
(B1/B2/B8 — info/konversi/resize) **TESTED** (belum VERIFIED). Phase 6 menata ulang tampilan
(sidebar, header, dasbor petak) tanpa mengubah logika bisnis. Modul lain menyusul.
Lihat `docs/CHANGELOG.md` untuk riwayat dan `docs/FEATURE_MATRIX.md` untuk status fitur.

## 2. Sumber Kebenaran (Source of Truth)

Urutan prioritas bila terjadi konflik:

1. `docs/SPECIFICATION.md` — spesifikasi teknis yang tidak ambigu.
2. `AGENTS.md` (dokumen ini) — aturan kerja.
3. `docs/FEATURE_MATRIX.md` — status setiap fitur.
4. `docs/TEST_PLAN.md` — rencana dan kriteria penerimaan pengujian.
5. `docs/ARCHITECTURE.md` — arsitektur dan batas modul.
6. `docs/SECURITY.md` — aturan keamanan, privasi, dan sumber daya.

Jangan mengubah keputusan arsitektur/keamanan/perilaku output tanpa pertanyaan tertulis dan
persetujuan pengguna (lihat bagian 10).

## 3. Aturan Mutlak

1. Jangan mengklaim sesuatu tanpa bukti. Bedakan selalu:
   - **IMPLEMENTED** — kode sudah ditulis.
   - **TESTED** — pengujian benar-benar dijalankan dan hasilnya nyata.
   - **VERIFIED** — memenuhi kriteria penerimaan dengan bukti.
   - **BLOCKED** — terhambat oleh kondisi tertentu.
   - **NOT IMPLEMENTED** — belum dibuat.
2. Jangan membuat tombol tanpa handler, progres palsu, atau data dummy yang tampak nyata.
3. Jangan menelan exception tanpa mencatat dan melaporkannya.
4. Jangan menimpa/menghapus file pengguna tanpa izin eksplisit.
5. Jangan menambahkan dependensi, menu, endpoint, atau fitur di luar `docs/SPECIFICATION.md`.
6. Jangan menurunkan standar tes agar jumlah tes lulus terlihat tinggi.
7. Fitur yang belum ada harus ditandai eksplisit, bukan disembunyikan dengan placeholder.

## 4. Stack Teknologi (terkunci)

- OS target: Windows 10/11 64-bit.
- Python: **3.12** (interpreter terverifikasi ada di environment; lihat bagian 7).
- UI: **PySide6**.
- PDF: **PyMuPDF** (manipulasi) dan **pypdf** (operasi struktural/ringan).
- Gambar: **Pillow**.
- QR generate: **qrcode**.
- QR decode: **opencv-python-headless** (`QRCodeDetector`). Menggantikan **zxing-cpp** karena
  import `.pyd`-nya diblokir Smart App Control pada mesin pengembangan; keputusan disetujui
  pengguna dan dicatat di `docs/SPECIFICATION.md` §3.3/§12. (Menambah `numpy`.)
- Tes: **pytest**, **pytest-qt**.
- Distribusi: **PyInstaller**.

Daftar versi terkunci ada di `docs/SPECIFICATION.md`. Jangan mengarang nomor versi.

## 5. Larangan Offline/Privasi

- Tidak ada cloud API, upload file, akun, atau telemetry.
- Tidak membuka URL dari dokumen/QR secara otomatis.
- Tidak ada pemeriksaan update jaringan otomatis.
- Semua resource UI (font, ikon, stylesheet) lokal.
- Jangan menghapus file sumber secara otomatis.
- Log tidak boleh memuat isi dokumen, kata sandi, atau data sensitif.

## 6. Konvensi Kode

- Type hints pada seluruh fungsi publik.
- Docstring pada modul dan fungsi kompleks.
- `pathlib` untuk manipulasi path.
- Hierarki exception kustom di `src/office_toolkit/core/errors.py`.
- Jangan membuat satu file besar; pisahkan per tanggung jawab.
- Jangan menambahkan komentar naratif yang tidak perlu.
- Bahasa antarmuka pengguna: **Indonesia**.

## 7. Environment Pengembangan (hasil audit Phase 0)

- Interpreter target: `py -3.12` →
  `C:\Users\Teknis KIP\AppData\Local\Programs\Python\Python312\python.exe` (Python 3.12.0).
- `python`/`pip` tidak ada di PATH; gunakan **`py -3.12 -m pip ...`**.
- Terpasang (3.12): PySide6 6.11.2, PyMuPDF 1.28.2, Pillow 11.3.0, pikepdf 9.11.0,
  pytest 9.1.1, PyInstaller 6.21.0, qrcode 8.2, opencv-python-headless 4.11.0.86, numpy 2.5.4.
- Belum terpasang (3.12): pypdf, pytest-qt. Tes UI memakai `QApplication` offscreen manual
  (`QT_QPA_PLATFORM=offscreen`) selama pytest-qt belum dipasang.
- Python 3.14.6 juga ada di `C:\Python314` — **jangan** dipakai untuk proyek ini.

Perintah standar (lihat juga `scripts/`):

```powershell
# setup environment
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt

# jalankan aplikasi
.\.venv\Scripts\python -m office_toolkit

# jalankan tes
.\.venv\Scripts\python -m pytest

# build Windows
.\scripts\build_windows.ps1
```

## 8. Struktur Proyek

Struktur target (lihat `docs/ARCHITECTURE.md`). Ringkas:

```
office-toolkit/
  AGENTS.md  README.md  pyproject.toml  requirements*.txt  app.spec
  docs/      assets/    scripts/
  src/office_toolkit/{core,ui,services,resources}
  tests/{unit,integration,ui,security,fixtures}
```

Aturan ketergantungan lapisan: `ui → services → core`. `core` tidak boleh mengimpor `ui`.
`services` tidak boleh mengimpor `ui`.

## 9. Definisi Selesai (Definition of Done)

Sebuah fitur hanya boleh ditandai selesai jika semua terpenuhi:

1. Implementasi nyata.
2. Validasi input.
3. Penanganan error.
4. Output dapat diverifikasi.
5. Tes relevan dijalankan dan lulus.
6. Dokumentasi diperbarui.
7. Tidak ada placeholder yang menyamar sebagai fitur selesai.

## 10. Kapan Harus Bertanya

Hentikan dan ajukan pertanyaan bila keputusan menyangkut: arsitektur, keamanan, format output,
dependensi baru, lisensi, atau perubahan spesifikasi. Untuk ambiguitas yang tidak menghalangi,
dokumentasikan asumsi aman lalu lanjutkan.

## 11. Commit

Jangan melakukan commit/push kecuali diminta eksplisit oleh pengguna.
