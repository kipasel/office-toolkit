"""Build a PDF from one or more local images (Phase 4, Fitur C).

Supported page sizes: image size, A4, and Letter. Orientation may be explicit
(portrait/landscape) or derived from the image. Images are never stretched:
placement modes keep the aspect ratio. Explicit transparency background handling
is applied (PDF pages are opaque), EXIF orientation is honored, and only the
first frame of multi-page TIFF files is used (warned explicitly). Source files
are never modified.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import pymupdf
from PIL import Image, ImageOps

from office_toolkit.core.config import get_config
from office_toolkit.core.errors import (
    ProcessingError,
    ResourceLimitError,
    ValidationError,
)
from office_toolkit.core.file_validation import validate_input_file
from office_toolkit.services.pdf.common import write_verified_pdf

PAGE_SIZE_IMAGE = "image"
PAGE_SIZE_A4 = "a4"
PAGE_SIZE_LETTER = "letter"

_MAP_PAGE_SIZE = {
    PAGE_SIZE_IMAGE: None,
    PAGE_SIZE_A4: (595.28, 841.89),
    PAGE_SIZE_LETTER: (612.0, 792.0),
}

ORIENTATION_PORTRAIT = "portrait"
ORIENTATION_LANDSCAPE = "landscape"
ORIENTATION_AUTO = "auto"

FIT_MODE_FIT = "fit"
FIT_MODE_ORIGINAL = "original"


@dataclass
class ImagesToPdfResult:
    output: Path
    page_count: int
    succeeded: List[Path]
    failed: List[Tuple[str, str]]
    warnings: List[str] = field(default_factory=list)


@dataclass
class _PreparedImage:
    data_png: bytes
    natural_w_pt: float
    natural_h_pt: float
    orientation: str
    source_name: str


def _open_single_frame(path: Path, warnings: List[str]) -> Image.Image:
    v = validate_input_file(path)
    if not v.valid:
        raise ValidationError(v.errors[0] if v.errors else f"File tidak valid: {path}")
    try:
        im = Image.open(path)
    except Exception as e:
        raise ProcessingError(f"Gagal membaca gambar {path.name}: {e}")
    limit = get_config().max_image_pixels
    if im.width and im.height and im.width * im.height > limit:
        im.close()
        raise ResourceLimitError(
            f"Gambar {path.name} melebihi batas {limit} piksel."
        )
    if getattr(im, "n_frames", 1) > 1:
        warnings.append(
            f"{path.name}: hanya halaman (frame) pertama dari TIFF/GIF multi-halaman yang diproses."
        )
        im.seek(0)
        frame = im.copy()
        im.close()
        im = frame
    transposed = ImageOps.exif_transpose(im)
    if transposed is not im:
        im.close()
    return transposed


def _prepare_image(path: Path, background: Optional[str], warnings: List[str]) -> _PreparedImage:
    im = _open_single_frame(path, warnings)
    try:
        if isinstance(im.info, dict):
            dpi = im.info.get("dpi")
        else:
            dpi = None
        try:
            dpi_x = float(dpi[0]) if dpi and dpi[0] else 72.0
            dpi_y = float(dpi[1]) if dpi and dpi[1] else 72.0
        except (TypeError, ValueError, IndexError):
            dpi_x = dpi_y = 72.0
        cfg = get_config()
        lo, hi = cfg.pdf_render_dpi_min, cfg.pdf_render_dpi_max
        if not lo <= dpi_x <= hi:
            dpi_x = 72.0
        if not lo <= dpi_y <= hi:
            dpi_y = 72.0
        natural_w_pt = im.width * 72.0 / dpi_x
        natural_h_pt = im.height * 72.0 / dpi_y
        orientation = ORIENTATION_PORTRAIT if im.height >= im.width else ORIENTATION_LANDSCAPE

        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            rgba = im.convert("RGBA")
            if background and background != "transparent":
                bg = Image.new("RGB", rgba.size, background)
                bg.paste(rgba, mask=rgba.split()[3])
                out = bg
            else:
                out = rgba
        else:
            out = im.convert("RGB")

        buf = io.BytesIO()
        out.save(buf, format="PNG")
        return _PreparedImage(
            data_png=buf.getvalue(),
            natural_w_pt=round(natural_w_pt, 2),
            natural_h_pt=round(natural_h_pt, 2),
            orientation=orientation,
            source_name=path.name,
        )
    finally:
        im.close()


def _page_dims(page_size: str, orientation: str, img: _PreparedImage) -> Tuple[float, float]:
    base = _MAP_PAGE_SIZE[page_size]
    if base is None:
        return img.natural_w_pt, img.natural_h_pt
    w, h = base
    orient = img.orientation if orientation == ORIENTATION_AUTO else orientation
    if orient == ORIENTATION_LANDSCAPE and h > w:
        w, h = h, w
    elif orient == ORIENTATION_PORTRAIT and w > h:
        w, h = h, w
    return w, h


def _content_rect(page_w: float, page_h: float, img: _PreparedImage, fit_mode: str, margin: float) -> Tuple[float, float, float, float]:
    max_w = max(1.0, page_w - 2 * margin)
    max_h = max(1.0, page_h - 2 * margin)
    ratio = img.natural_h_pt / img.natural_w_pt if img.natural_w_pt else 1.0

    if fit_mode == FIT_MODE_ORIGINAL:
        w, h = img.natural_w_pt, img.natural_h_pt
        if w > max_w or h > max_h:
            scale = min(max_w / w, max_h / h)
            w, h = w * scale, h * scale
    else:
        w = min(max_w, img.natural_w_pt)
        h = w * ratio
        if h > max_h:
            h = max_h
            w = h / ratio

    x = (page_w - w) / 2.0
    y = (page_h - h) / 2.0
    return x, y, w, h


def images_to_pdf(
    image_paths: Sequence[str | Path],
    output_dir: str | Path,
    *,
    page_size: str = PAGE_SIZE_IMAGE,
    orientation: str = "auto",
    fit_mode: str = FIT_MODE_FIT,
    margin_pt: float = 0.0,
    background: str = "white",
    output_name: Optional[str] = None,
) -> ImagesToPdfResult:
    """Create a single PDF from images, preserving the given order.

    ``margin_pt`` must be >= 0. ``background`` is any Pillow color name or hex
    ('white'/'black' work as expected); 'transparent' keeps alpha where possible.
    """
    if page_size not in _MAP_PAGE_SIZE:
        raise ValidationError(
            f"Ukuran halaman tidak didukung: {page_size} (pilihan: {', '.join(_MAP_PAGE_SIZE)})"
        )
    if orientation not in (ORIENTATION_AUTO, ORIENTATION_PORTRAIT, ORIENTATION_LANDSCAPE):
        raise ValidationError(f"Orientasi tidak didukung: {orientation}")
    if fit_mode not in (FIT_MODE_FIT, FIT_MODE_ORIGINAL):
        raise ValidationError(f"Mode penempatan tidak didukung: {fit_mode}")
    if margin_pt < 0:
        raise ValidationError("Margin tidak boleh negatif.")

    paths = [Path(p) for p in image_paths]
    if not paths:
        raise ValidationError("Pilih minimal satu gambar terlebih dahulu.")

    out_dir = Path(output_dir)
    src = paths[0]
    name = output_name or "dokumen_gambar.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    from office_toolkit.services.pdf.common import safe_output_path

    out_path = safe_output_path(out_dir, name, allow_overwrite=False)

    warnings: List[str] = []
    succeeded: List[Path] = []
    failed: List[Tuple[str, str]] = []

    doc = pymupdf.open()
    try:
        for p in paths:
            try:
                img = _prepare_image(p, background, warnings)
                pw, ph = _page_dims(page_size, orientation, img)
                x, y, w, h = _content_rect(pw, ph, img, fit_mode, margin_pt)
                page = doc.new_page(width=pw, height=ph)
                page.insert_image(
                    pymupdf.Rect(x, y, x + w, y + h),
                    stream=img.data_png,
                    keep_proportion=True,
                    overlay=True,
                )
                succeeded.append(p)
            except ResourceLimitError:
                raise  # policy violation: fail fast rather than continue
            except Exception as e:
                failed.append((p.name, str(e)))

        if not succeeded:
            raise ProcessingError("Tidak ada gambar yang berhasil diproses menjadi PDF.")

        write_verified_pdf(
            doc,
            out_path,
            len(succeeded),
            garbage=4,
            deflate=True,
            deflate_images=True,
        )
    finally:
        doc.close()

    for name, err in failed:
        warnings.append(f"{name}: {err}")

    return ImagesToPdfResult(
        output=out_path,
        page_count=len(succeeded),
        succeeded=succeeded,
        failed=failed,
        warnings=warnings,
    )