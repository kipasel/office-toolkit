"""Render PDF pages to PNG/JPEG images (Phase 4, Fitur B).

Pages are rendered one at a time (never the whole document in memory at once),
respecting the documented DPI limits. Output names are ``<stem>_page_001.png``
so page ordering sorts naturally and collisions are avoided via OutputManager.
Per-page failures are reported; raster output does not contain selectable text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Union

import pymupdf

from office_toolkit.core.errors import (
    ProcessingError,
    ValidationError,
)
from office_toolkit.services.pdf.common import (
    check_render_limits,
    open_pdf,
    resolve_pages,
    safe_output_path,
    write_image_bytes,
)

SUPPORTED_FORMATS = ("png", "jpg", "jpeg")


@dataclass
class RenderedPageFile:
    page: int
    output: Path
    size_bytes: int


@dataclass
class RenderResult:
    input: Path
    format: str
    dpi: int
    page_count: int
    outputs: List[RenderedPageFile] = field(default_factory=list)
    failed: List[int] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def rendered_count(self) -> int:
        return len(self.outputs)


def render_pdf_to_images(
    input_path: str | Path,
    output_dir: str | Path,
    pages: Union[str, Optional[Sequence[int]]] = None,
    fmt: str = "png",
    dpi: int = 150,
    base_name: Optional[str] = None,
) -> RenderResult:
    """Render selected pages (or all) of a PDF to PNG/JPEG images."""
    img_fmt = fmt.lower().strip()
    if img_fmt not in SUPPORTED_FORMATS:
        raise ValidationError(
            f"Format tidak didukung: {fmt} (pilihan: {', '.join(SUPPORTED_FORMATS)})"
        )
    ext = "png" if img_fmt == "png" else "jpg"

    src = Path(input_path)
    out_dir = Path(output_dir)
    doc = open_pdf(src)
    try:
        count = doc.page_count
        if count <= 0:
            raise ValidationError("Dokumen tidak memiliki halaman.")
        check_render_limits(count, dpi)

        if pages is None:
            selected = list(range(1, count + 1))
        else:
            selected = resolve_pages(pages, count)

        width = max(3, len(str(count)))
        stem = base_name or src.stem
        outputs: List[RenderedPageFile] = []
        failed: List[int] = []
        warnings: List[str] = []

        for n in selected:
            out_path = safe_output_path(
                out_dir, f"{stem}_page_{n:0{width}d}.{ext}", allow_overwrite=False
            )
            try:
                pix = doc[n - 1].get_pixmap(
                    dpi=dpi, colorspace=pymupdf.csRGB, alpha=False
                )
                data = pix.tobytes("png" if img_fmt == "png" else "jpeg")
                write_image_bytes(data, out_path, f".{ext}")
                outputs.append(
                    RenderedPageFile(
                        page=n, output=out_path, size_bytes=out_path.stat().st_size
                    )
                )
            except Exception as e:
                failed.append(n)
                warnings.append(f"Halaman {n} gagal dirender: {e}")

        if not outputs:
            raise ProcessingError("Tidak ada halaman yang berhasil dirender.")
        warnings.append(
            "Hasil render berupa gambar raster; teks di dalamnya tidak dapat dipilih/disalin."
        )
        return RenderResult(
            input=src,
            format=img_fmt,
            dpi=dpi,
            page_count=len(selected),
            outputs=outputs,
            failed=failed,
            warnings=warnings,
        )
    finally:
        doc.close()