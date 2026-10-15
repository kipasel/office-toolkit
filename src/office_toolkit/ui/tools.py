"""Registered tools shown as Metro tiles and searchable in the header.

This registry is the single source of truth for the dashboard and the header
search. Every entry maps to a real workspace page/tab, except entries flagged
``available=False`` which represent tools that are explicitly **not implemented
yet** and are rendered as disabled tiles (never as fake/simulated features).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

# Page indexes must match the QStackedWidget order in MainWindow.
PAGE_DASHBOARD = 0
PAGE_PDF = 1
PAGE_PDF_ADVANCED = 2
PAGE_QR = 3
PAGE_IMAGE = 4


@dataclass(frozen=True)
class Tool:
    id: str
    name: str
    description: str
    category: str
    icon: str
    page: Optional[int] = None
    tab: Optional[int] = None
    available: bool = True


@dataclass(frozen=True)
class Category:
    id: str
    title: str
    color: str


CATEGORIES: List[Category] = [
    Category("gambar", "Gambar", "#0F9D8A"),
    Category("pdf", "PDF", "#E45B65"),
    Category("qr", "QR Code", "#7657D5"),
    Category("file", "File & Dokumen", "#E88A24"),
]


TOOLS: List[Tool] = [
    # -- Gambar (implemented: info / convert / resize) -----------------
    Tool("info_gambar", "Info Gambar", "Format, dimensi, ukuran, transparansi.",
         "gambar", "info", PAGE_IMAGE, 0),
    Tool("konversi_gambar", "Ubah Format Gambar", "PNG, JPEG, WebP, BMP, TIFF.",
         "gambar", "convert", PAGE_IMAGE, 1),
    Tool("resize_gambar", "Ubah Ukuran Gambar", "Lebar menjaga rasio atau persentase.",
         "gambar", "resize", PAGE_IMAGE, 2),
    Tool("kompres_gambar", "Kompres Gambar", "Belum tersedia.",
         "gambar", "compress", available=False),
    Tool("crop_rotate_gambar", "Crop dan Rotasi", "Belum tersedia.",
         "gambar", "crop", available=False),
    # -- PDF ------------------------------------------------------------
    Tool("info_pdf", "Info PDF", "Metadata, jumlah halaman, status enkripsi.",
         "pdf", "info", PAGE_PDF, 0),
    Tool("gabung_pdf", "Gabung PDF", "Satukan beberapa PDF, urutan bisa diatur.",
         "pdf", "merge", PAGE_PDF, 1),
    Tool("pisah_pdf", "Pisah PDF", "Berdasarkan rentang atau per halaman.",
         "pdf", "split", PAGE_PDF, 2),
    Tool("ekstrak_pdf", "Ekstrak Halaman", "Ambil halaman tertentu.",
         "pdf", "extract", PAGE_PDF, 3),
    Tool("susun_pdf", "Susun Ulang", "Ubah urutan halaman.",
         "pdf", "reorder", PAGE_PDF, 4),
    Tool("rotasi_pdf", "Rotasi Halaman", "Putar 90/180/270 derajat.",
         "pdf", "rotate", PAGE_PDF, 5),
    Tool("kompres_pdf", "Kompres PDF", "Lossless, kompresi gambar, atau rasterisasi.",
         "pdf", "compress", PAGE_PDF_ADVANCED, 0),
    Tool("pdf_ke_gambar", "PDF ke Gambar", "Render per halaman ke PNG/JPEG.",
         "pdf", "to_image", PAGE_PDF_ADVANCED, 1),
    Tool("gambar_ke_pdf", "Gambar ke PDF", "Satukan gambar menjadi PDF.",
         "pdf", "from_image", PAGE_PDF_ADVANCED, 2),
    Tool("tambah_teks_pdf", "Tambah Teks", "Tambahkan kotak teks ke halaman.",
         "pdf", "text", PAGE_PDF_ADVANCED, 3),
    Tool("tambah_gambar_pdf", "Tambah Gambar", "Sisipkan gambar ke halaman.",
         "pdf", "image_add", PAGE_PDF_ADVANCED, 4),
    Tool("anotasi_pdf", "Anotasi", "Highlight, catatan, kotak, garis/panah.",
         "pdf", "annotate", PAGE_PDF_ADVANCED, 5),
    Tool("tanda_tangan_pdf", "Tanda Tangan Gambar", "Tempel gambar tanda tangan.",
         "pdf", "signature", PAGE_PDF_ADVANCED, 6),
    Tool("proteksi_pdf", "Proteksi PDF", "Kata sandi AES-256/128.",
         "pdf", "lock", PAGE_PDF_ADVANCED, 7),
    Tool("buka_proteksi_pdf", "Buka Proteksi", "Hapus proteksi dengan kata sandi diketahui.",
         "pdf", "unlock", PAGE_PDF_ADVANCED, 8),
    # -- QR Code --------------------------------------------------------
    Tool("buat_qr", "Buat QR Code", "Teks, URL, atau nomor dengan gaya sendiri.",
         "qr", "qr", PAGE_QR, 0),
    Tool("qr_massal", "QR Code Massal", "Buat banyak QR dari file CSV.",
         "qr", "batch", PAGE_QR, 1),
    Tool("baca_qr", "Baca QR Code", "Baca QR dari gambar lokal.",
         "qr", "search", PAGE_QR, 2),
    # -- File & Dokumen (not implemented) -------------------------------
    Tool("rename_massal", "Ubah Nama Banyak File", "Belum tersedia.",
         "file", "rename", available=False),
    Tool("cari_duplikat", "Cari File Duplikat", "Belum tersedia.",
         "file", "duplicate", available=False),
    Tool("ekspor_daftar", "Ekspor Daftar File", "Belum tersedia.",
         "file", "export", available=False),
    Tool("json_formatter", "JSON Formatter", "Belum tersedia.",
         "file", "json", available=False),
    Tool("csv_validator", "CSV Validator", "Belum tersedia.",
         "file", "csv", available=False),
    Tool("text_encoding", "Text Encoding Tools", "Belum tersedia.",
         "file", "encoding", available=False),
]


def search_tools(query: str) -> List[Tool]:
    """Return tools whose name/description/category matches ``query``."""
    q = (query or "").strip().lower()
    if not q:
        return list(TOOLS)
    matches: List[Tool] = []
    for tool in TOOLS:
        haystack = f"{tool.name} {tool.description} {tool.category}".lower()
        if q in haystack:
            matches.append(tool)
    return matches


def category_of(category_id: str) -> Category:
    for cat in CATEGORIES:
        if cat.id == category_id:
            return cat
    return Category(category_id, category_id, "#2563EB")
