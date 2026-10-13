"""PDF compression (Phase 4, Fitur A).

Modes:
- ``struktur``  : lossless structural optimization (garbage collection, deflate,
                  object streams). No rasterization; text, links, bookmarks and
                  forms are preserved as far as the library permits.
- ``images``    : lossy embedded-image optimization using ``rewrite_images``
                  (JPEG recompression / optional dpi target). Text stays.
- ``rasterize`` : aggressive lossy mode. Every page is rendered to a raster image
                  at an explicit DPI. Text, links, bookmarks and forms are lost;
                  the caller must warn the user before running.

Compression is not guaranteed to reduce the file; raw sizes and the savings
percentage are always reported. ``savings_pct < 0`` means the result is larger.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import pymupdf

from office_toolkit.core.config import get_config
from office_toolkit.core.errors import (
    OutputError,
    ProcessingError,
    ResourceLimitError,
    ValidationError,
)
from office_toolkit.services.pdf.common import (
    check_render_limits,
    open_pdf,
    savings_percent,
    write_verified_pdf,
)

MODE_STRUCTURE = "struktur"
MODE_IMAGES = "images"
MODE_RASTERIZE = "rasterize"

SUPPORTED_MODES = (MODE_STRUCTURE, MODE_IMAGES, MODE_RASTERIZE)


@dataclass
class CompressResult:
    input: Path
    output: Path
    mode: str
    input_size: int
    output_size: int
    savings_pct: float
    page_count: int
    warnings: List[str] = field(default_factory=list)


def validate_mode(mode: str) -> None:
    if mode not in SUPPORTED_MODES:
        raise ValidationError(
            f"Mode kompresi tidak didukung: {mode} (pilihan: {', '.join(SUPPORTED_MODES)})"
        )


def _rasterize(doc: pymupdf.Document, out_path: Path, dpi: int) -> None:
    """Render every page at ``dpi`` into a brand-new PDF (text/link loss)."""
    count = doc.page_count
    check_render_limits(count, dpi)
    new = pymupdf.open()
    try:
        for page in doc:
            pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
            np = new.new_page(width=page.rect.width, height=page.rect.height)
            np.insert_image(np.rect, pixmap=pix, keep_proportion=False)
        write_verified_pdf(
            new,
            out_path,
            count,
            garbage=4,
            deflate=True,
            deflate_images=True,
        )
    finally:
        new.close()


def compress_pdf(
    input_path: str | Path,
    output_dir: str | Path,
    mode: str = MODE_STRUCTURE,
    *,
    quality: int = 80,
    image_dpi_target: int = 0,
    rasterize_dpi: int = 150,
    output_name: Optional[str] = None,
) -> CompressResult:
    """Compress a PDF into a new file (source is never modified).

    ``quality`` (1-100) applies to the lossy image mode. ``image_dpi_target``
    (0 = keep, otherwise target DPI) and ``rasterize_dpi`` follow the documented
    DPI limits.
    """
    validate_mode(mode)
    if not 1 <= quality <= 100:
        raise ValidationError("Kualitas kompresi harus antara 1 dan 100.")
    if image_dpi_target:
        cfg = get_config()
        if not cfg.pdf_render_dpi_min <= image_dpi_target <= cfg.pdf_render_dpi_max:
            raise ValidationError(
                f"Target DPI gambar harus antara {cfg.pdf_render_dpi_min} dan {cfg.pdf_render_dpi_max}."
            )

    src = Path(input_path)
    out_dir = Path(output_dir)
    doc = open_pdf(src)
    warnings: List[str] = []
    try:
        count = doc.page_count
        out_path = safe_compress_path(src, out_dir, mode, output_name)
        if mode == MODE_STRUCTURE:
            write_verified_pdf(
                doc,
                out_path,
                count,
                garbage=4,
                deflate=True,
                clean=True,
                deflate_images=True,
                deflate_fonts=True,
                use_objstms=1,
                preserve_metadata=True,
            )
        elif mode == MODE_IMAGES:
            warnings.append(
                "Optimasi gambar bersifat lossy (rekompresi JPEG); kualitas visual dapat menurun."
            )
            if image_dpi_target:
                warnings.append(
                    f"Resolusi gambar tertanam diarahkan ke ±{image_dpi_target} DPI."
                )
            try:
                doc.rewrite_images(
                    dpi_threshold=image_dpi_target or None,
                    dpi_target=image_dpi_target,
                    quality=quality,
                    lossy=True,
                    lossless=True,
                    bitonal=True,
                    color=True,
                    gray=True,
                )
            except Exception as e:
                raise ProcessingError(f"Gagal mengoptimasi gambar tertanam: {e}")
            write_verified_pdf(
                doc,
                out_path,
                count,
                garbage=4,
                deflate=True,
                deflate_images=True,
                preserve_metadata=True,
            )
        else:
            warnings.append(
                "Mode rasterisasi mengubah setiap halaman menjadi gambar; "
                "teks dapat dicari, tautan, bookmark, formulir, dan anotasi TIDAK dipertahankan."
            )
            _rasterize(doc, out_path, rasterize_dpi)
    finally:
        doc.close()

    out_size = out_path.stat().st_size
    in_size = src.stat().st_size
    return CompressResult(
        input=src,
        output=out_path,
        mode=mode,
        input_size=in_size,
        output_size=out_size,
        savings_pct=savings_percent(in_size, out_size),
        page_count=count,
        warnings=warnings,
    )


def safe_compress_path(
    src: Path, out_dir: Path, mode: str, output_name: Optional[str]
) -> Path:
    from office_toolkit.services.pdf.common import safe_output_path

    name = output_name or f"{src.stem}_kompres_{mode}.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return safe_output_path(out_dir, name, allow_overwrite=False)