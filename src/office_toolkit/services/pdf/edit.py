"""Add text, images, annotations, and image signatures to PDFs (Phase 4, Fitur D-G).

All operations produce a *new* file; the source is never modified. Inserted text
uses the built-in Helvetica font (Latin coverage); characters outside Latin-1 fall
back to a locally available system font or produce an explicit warning. Placing an
image preserves its aspect ratio and never silently drops content out of the page.
Image signatures are image placements only - they are NOT certified digital
signatures and carry no identity or integrity guarantee.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import pymupdf
from PIL import Image

from office_toolkit.core.config import get_config
from office_toolkit.core.errors import (
    ProcessingError,
    ResourceLimitError,
    ValidationError,
)
from office_toolkit.core.file_validation import validate_input_file
from office_toolkit.services.pdf.common import (
    open_pdf,
    resolve_pages,
    safe_output_path,
    write_verified_pdf,
)

TEXT_ALIGN_MAP = {
    "left": pymupdf.TEXT_ALIGN_LEFT,
    "center": pymupdf.TEXT_ALIGN_CENTER,
    "right": pymupdf.TEXT_ALIGN_RIGHT,
    "justify": pymupdf.TEXT_ALIGN_JUSTIFY,
}

_FALLBACK_FONTS = [
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/calibri.ttf"),
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("C:/Windows/Fonts/times.ttf"),
]


def _find_fallback_font() -> Optional[Path]:
    for p in _FALLBACK_FONTS:
        if p.exists():
            return p
    return None


def _validate_color(color: Tuple[float, float, float]) -> None:
    if len(color) != 3:
        raise ValidationError("Warna harus berupa triplet RGB.")
    for c in color:
        if not 0.0 <= c <= 1.0:
            raise ValidationError("Komponen warna harus antara 0 dan 1.")


def _validate_image(path: Path) -> tuple[int, int]:
    v = validate_input_file(path)
    if not v.valid:
        raise ValidationError(v.errors[0] if v.errors else "Gambar tidak valid.")
    with Image.open(path) as im:
        im.load()
        limit = get_config().max_image_pixels
        if im.width and im.height and im.width * im.height > limit:
            raise ResourceLimitError(
                f"Gambar melebihi batas {limit} piksel: {path.name}"
            )
        return im.width, im.height


# --------------------------------------------------------------------------- text
@dataclass
class AddTextResult:
    input: Path
    output: Path
    page_count: int
    inserted_pages: List[int]
    warnings: List[str] = field(default_factory=list)


def add_text_to_pdf(
    input_path: str | Path,
    text: str,
    pages: Union[str, Sequence[int]],
    output_dir: str | Path,
    *,
    x: float = 50.0,
    y: float = 50.0,
    box_width: float = 300.0,
    fontsize: float = 12.0,
    color: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    align: str = "left",
    output_name: Optional[str] = None,
) -> AddTextResult:
    """Insert ``text`` into selected pages at (``x``, ``y``) using a text box."""
    if not text or not text.strip():
        raise ValidationError("Teks tidak boleh kosong.")
    if align not in TEXT_ALIGN_MAP:
        raise ValidationError(f"Perataan tidak didukung: {align}")
    if fontsize <= 0:
        raise ValidationError("Ukuran teks harus > 0.")
    if box_width <= 0:
        raise ValidationError("Lebar kotak teks harus > 0.")
    _validate_color(color)

    src = Path(input_path)
    doc = open_pdf(src)
    try:
        count = doc.page_count
        selected = resolve_pages(pages, count)
        out_path = safe_output_path(
            Path(output_dir), (output_name or f"{src.stem}_teks.pdf"), allow_overwrite=False
        )
        warnings: List[str] = []

        fontname = "helv"
        fontfile: Optional[str] = None
        glyph_uncertain = False
        try:
            text.encode("latin-1")
        except UnicodeEncodeError:
            fb = _find_fallback_font()
            if fb:
                fontname = "f0"
                fontfile = str(fb)
            else:
                glyph_uncertain = True
                warnings.append(
                    "Teks memuat karakter di luar Latin-1; font dasar Helvetica tidak "
                    "mewakili semuanya, sebagian karakter mungkin tidak dirender."
                )

        for n in selected:
            page = doc[n - 1]
            pr = page.rect
            if x < 0 or y < 0 or x >= pr.width or y >= pr.height:
                raise ValidationError(
                    f"Koordinat ({x}, {y}) berada di luar halaman {n}."
                )
            width = min(box_width, pr.width - x)
            if width <= 0:
                raise ValidationError(f"Tidak ada ruang untuk teks pada halaman {n}.")
            rect = pymupdf.Rect(x, y, x + width, pr.height)
            overflow = page.insert_textbox(
                rect,
                text,
                fontsize=fontsize,
                fontname=fontname,
                fontfile=fontfile,
                color=color,
                align=TEXT_ALIGN_MAP[align],
                overlay=True,
            )
            if overflow < 0:
                warnings.append(
                    f"Halaman {n}: teks terlalu panjang untuk area yang ditentukan; "
                    "ditampilkan sebagian."
                )
            elif box_width > (pr.width - x):
                warnings.append(
                    f"Halaman {n}: lebar kotak melebihi batas halaman; diperkecil agar pas."
                )

        write_verified_pdf(
            doc, out_path, count, garbage=4, deflate=True, preserve_metadata=True
        )
    finally:
        doc.close()

    if not glyph_uncertain:
        verify_text_present(out_path, selected, text, warnings)
    return AddTextResult(
        input=src,
        output=out_path,
        page_count=count,
        inserted_pages=selected,
        warnings=warnings,
    )


def verify_text_present(out_path: Path, pages: Sequence[int], text: str, warnings: List[str]) -> None:
    target = "".join(text.split()).lower()
    if not target:
        return
    with pymupdf.open(str(out_path)) as check:
        found = any(
            target in "".join(check[n - 1].get_text().split()).lower() for n in pages
        )
    if not found:
        raise ProcessingError(
            "Verifikasi gagal: teks yang ditambahkan tidak ditemukan pada hasil PDF."
        )


# -------------------------------------------------------------------------- image
@dataclass
class AddImageResult:
    input: Path
    output: Path
    page_count: int
    placed_pages: List[int]
    rect: Tuple[float, float, float, float]
    warnings: List[str] = field(default_factory=list)


def add_image_to_pdf(
    input_path: str | Path,
    image_path: str | Path,
    pages: Union[str, Sequence[int]],
    output_dir: str | Path,
    *,
    x: float = 0.0,
    y: float = 0.0,
    width_pt: Optional[float] = None,
    height_pt: Optional[float] = None,
    keep_proportion: bool = True,
    output_name: Optional[str] = None,
) -> AddImageResult:
    """Place an image at (``x``, ``y``) with an explicit or computed size."""
    img = Path(image_path)
    img_w, img_h = _validate_image(img)
    aspect = img_w / img_h if img_h else 1.0

    if width_pt is not None and width_pt <= 0:
        raise ValidationError("Lebar gambar harus > 0.")
    if height_pt is not None and height_pt <= 0:
        raise ValidationError("Tinggi gambar harus > 0.")

    if width_pt is None and height_pt is None:
        w = img_w
        h = img_h
    elif width_pt is not None and height_pt is None:
        w = width_pt
        h = w / aspect
    elif width_pt is None:
        h = height_pt
        w = h * aspect
    else:
        w = width_pt
        h = w / aspect
    if not keep_proportion and height_pt is not None and width_pt is not None:
        h = height_pt
        w = width_pt

    src = Path(input_path)
    doc = open_pdf(src)
    warnings: List[str] = []
    try:
        count = doc.page_count
        selected = resolve_pages(pages, count)
        out_path = safe_output_path(
            Path(output_dir), (output_name or f"{src.stem}_gambar.pdf"), allow_overwrite=False
        )

        width_px_pt = w
        height_px_pt = h
        first = selected[0]
        pr = doc[first - 1].rect
        max_w = pr.width - x
        max_h = pr.height - y
        if x < 0 or y < 0:
            raise ValidationError("Koordinat gambar tidak boleh negatif.")
        if x >= pr.width or y >= pr.height:
            raise ValidationError(f"Posisi gambar ({x}, {y}) berada di luar halaman {first}.")
        if width_px_pt > max_w or height_px_pt > max_h:
            scale = min(max_w / width_px_pt, max_h / height_px_pt, 1.0)
            w, h = width_px_pt * scale, height_px_pt * scale
            warnings.append(
                f"Gambar diperkecil agar berada dalam halaman (posisi {x},{y})."
            )

        rect = pymupdf.Rect(x, y, x + w, y + h)
        before = [len(doc[n - 1].get_images(full=True)) for n in selected]

        for n in selected:
            page = doc[n - 1]
            page.insert_image(
                rect, filename=str(img), keep_proportion=True, overlay=True
            )

        after = [len(doc[n - 1].get_images(full=True)) for n in selected]
        for n, (b, a) in zip(selected, zip(before, after)):
            if a <= b:
                warnings.append(f"Halaman {n}: gambar mungkin tidak tertanaman (tidak ada image XObject baru).")

        write_verified_pdf(
            doc, out_path, count, garbage=4, deflate=True, deflate_images=True,
            preserve_metadata=True,
        )
    finally:
        doc.close()

    return AddImageResult(
        input=src,
        output=out_path,
        page_count=count,
        placed_pages=selected,
        rect=(x, y, w, h),
        warnings=warnings,
    )


# ----------------------------------------------------------------- annotation
@dataclass
class AnnotateResult:
    input: Path
    output: Path
    page_count: int
    annots_added: int
    not_found: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def annotate_pdf(
    input_path: str | Path,
    pages: Union[str, Sequence[int]],
    output_dir: str | Path,
    *,
    annot_type: str,
    highlight_text: Optional[str] = None,
    note_pos: Optional[Tuple[float, float]] = None,
    note_text: Optional[str] = None,
    rect: Optional[Tuple[float, float, float, float]] = None,
    line_p1: Optional[Tuple[float, float]] = None,
    line_p2: Optional[Tuple[float, float]] = None,
    arrow: bool = False,
    color: Tuple[float, float, float] = (1.0, 0.8, 0.2),
    opacity: float = 0.8,
    output_name: Optional[str] = None,
) -> AnnotateResult:
    """Add a supported annotation type to selected pages.

    Supported types: ``highlight``, ``note``, ``rect``, ``line`` (arrow optional).
    Highlights require the target text to be found; a missing match is reported in
    ``not_found`` and never synthesizes a fake highlight.
    """
    if annot_type not in ("highlight", "note", "rect", "line"):
        raise ValidationError(f"Jenis anotasi tidak didukung: {annot_type}")
    if not 0.0 <= opacity <= 1.0:
        raise ValidationError("Opacity harus antara 0 dan 1.")
    _validate_color(color)

    src = Path(input_path)
    doc = open_pdf(src)
    added = 0
    not_found: List[str] = []
    warnings: List[str] = []
    try:
        count = doc.page_count
        selected = resolve_pages(pages, count)
        out_path = safe_output_path(
            Path(output_dir), (output_name or f"{src.stem}_anotasi.pdf"), allow_overwrite=False
        )
        for n in selected:
            page = doc[n - 1]
            pr = page.rect
            if annot_type == "highlight":
                target = (highlight_text or "").strip()
                if not target:
                    raise ValidationError("Teks untuk highlight tidak boleh kosong.")
                quads = page.search_for(target, quads=True)
                if not quads:
                    not_found.append(f"Halaman {n}: teks '{target}' tidak ditemukan; tidak dibuat highlight palsu.")
                    continue
                annot = page.add_highlight_annot(quads=quads)
                annot.set_colors(stroke=color)
                annot.set_opacity(opacity)
                annot.update()
                added += 1
            elif annot_type == "note":
                if note_pos is None or not note_text:
                    raise ValidationError("Catatan memerlukan posisi dan isi catatan.")
                x, y = note_pos
                if not (0 <= x < pr.width and 0 <= y < pr.height):
                    raise ValidationError(f"Posisi catatan di luar halaman {n}.")
                annot = page.add_text_annot(pymupdf.Point(x, y), note_text)
                annot.set_colors(stroke=color)
                annot.update()
                added += 1
            elif annot_type == "rect":
                if rect is None:
                    raise ValidationError("Kotak anotasi memerlukan koordinat.")
                r = pymupdf.Rect(*rect)
                if r.width <= 0 or r.height <= 0:
                    raise ValidationError("Dimensi kotak anotasi tidak valid (harus > 0).")
                if r.x1 > pr.width or r.y1 > pr.height or r.x0 < 0 or r.y0 < 0:
                    warnings.append(f"Halaman {n}: kotak anotasi melewati batas halaman.")
                annot = page.add_rect_annot(r)
                annot.set_colors(stroke=color)
                annot.set_opacity(opacity)
                annot.update()
                added += 1
            else:  # line / arrow
                if line_p1 is None or line_p2 is None:
                    raise ValidationError("Garis memerlukan dua titik.")
                p1 = pymupdf.Point(*line_p1)
                p2 = pymupdf.Point(*line_p2)
                annot = page.add_line_annot(p1, p2)
                if arrow:
                    annot.set_line_ends(
                        pymupdf.PDF_ANNOT_LE_NONE, pymupdf.PDF_ANNOT_LE_CLOSED_ARROW
                    )
                annot.set_colors(stroke=color)
                annot.set_opacity(opacity)
                annot.update()
                added += 1

        if annot_type in ("highlight",) and not_found:
            warnings.extend(not_found)

        write_verified_pdf(
            doc, out_path, count, garbage=4, deflate=True, preserve_metadata=True
        )
    finally:
        doc.close()

    # Verify annotations present on output (only pages that were annotated).
    read_back = verify_annotations(out_path, selected)
    for msg in read_back:
        warnings.append(msg)
    return AnnotateResult(
        input=src,
        output=out_path,
        page_count=count,
        annots_added=added,
        not_found=not_found,
        warnings=warnings,
    )


def verify_annotations(out_path: Path, pages: Sequence[int]) -> List[str]:
    messages: List[str] = []
    with pymupdf.open(str(out_path)) as check:
        for n in pages:
            annots = check[n - 1].annots()
            if annots is None or len(list(annots)) == 0:
                messages.append(f"Verifikasi: tidak ada anotasi terbaca pada halaman {n}.")
    return messages


# ----------------------------------------------------------------- signature
@dataclass
class SignatureResult:
    input: Path
    output: Path
    page_count: int
    placed_page: int
    rect: Tuple[float, float, float, float]
    warnings: List[str] = field(default_factory=list)


def add_signature_image(
    input_path: str | Path,
    image_path: str | Path,
    page: int,
    output_dir: str | Path,
    *,
    x: float = 0.0,
    y: float = 0.0,
    width_pt: Optional[float] = None,
    height_pt: Optional[float] = None,
    output_name: Optional[str] = None,
) -> SignatureResult:
    """Place a signature image on a single page as a new PDF file.

    Security note: this is an *image* only. It is NOT a certified digital
    signature, does not identify the signer, and does not provide cryptographic
    integrity. The image can be copied or moved by others.
    """
    res = add_image_to_pdf(
        input_path,
        image_path,
        str(page),
        output_dir,
        x=x,
        y=y,
        width_pt=width_pt,
        height_pt=height_pt,
        keep_proportion=True,
        output_name=output_name,
    )
    warnings = [
        "Ini BUKAN tanda tangan digital bersertifikat: tidak menjamin identitas "
        "penandatangan, integritas kriptografis, atau keaslian dokumen. "
        "Gambar tanda tangan dapat disalin/dipindahkan pihak lain."
    ] + list(res.warnings)
    return SignatureResult(
        input=res.input,
        output=res.output,
        page_count=res.page_count,
        placed_page=res.placed_pages[0] if res.placed_pages else page,
        rect=res.rect,
        warnings=warnings,
    )