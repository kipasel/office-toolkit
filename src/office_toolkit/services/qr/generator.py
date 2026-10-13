"""QR generation and export (Phase 5, Modul C - C1..C4).

Offline QR building from text/URL/number, design settings (module size, quiet
zone, colours, error correction), optional centre logo, and PNG/SVG export.
Generated files are written through ``OutputManager`` with verify-before-rename.
Payloads are never logged and no URL is opened automatically.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import qrcode
from qrcode import constants as qr_constants
from qrcode.exceptions import DataOverflowError

from office_toolkit.core.config import get_config
from office_toolkit.core.errors import ValidationError
from office_toolkit.core.file_validation import validate_input_file

from .common import (
    hex_to_rgb,
    low_contrast_warning,
    safe_output_path,
    write_verified_content,
)

ECC_LEVELS = ("L", "M", "Q", "H")
ECC_LABELS = {
    "L": "L (7% kerusakan)",
    "M": "M (15% kerusakan)",
    "Q": "Q (25% kerusakan)",
    "H": "H (30% kerusakan)",
}
MIN_QUIET_ZONE = 4
MAX_LOGO_FRACTION = 0.30
DEFAULT_LOGO_FRACTION = 0.20


@dataclass
class QrDesign:
    """Design settings applied to every generated QR code."""

    box_size: int = 8
    border: int = 4
    fg_color: str = "#000000"
    bg_color: str = "#FFFFFF"
    error_correction: str = "H"
    logo_path: Optional[str | Path] = None
    logo_fraction: float = DEFAULT_LOGO_FRACTION


@dataclass
class QrOutput:
    """Result of a single QR export."""

    output: Path
    fmt: str
    warnings: List[str] = field(default_factory=list)


def validate_design(design: QrDesign) -> List[str]:
    """Validate design values; return non-fatal warnings.

    Raises ``ValidationError`` for invalid values (empty data is validated in
    ``build_qr_image`` since it is payload, not design).
    """
    warnings: List[str] = []
    if design.box_size < 1:
        raise ValidationError("Ukuran modul harus minimal 1 piksel.")
    if design.border < 0:
        raise ValidationError("Quiet zone tidak boleh negatif.")
    if design.border < MIN_QUIET_ZONE and design.border >= 0:
        warnings.append(
            f"Quiet zone kecil ({design.border} modul; disarankan minimal "
            f"{MIN_QUIET_ZONE} modul) dapat mengurangi keterbacaan."
        )
    if design.error_correction not in ECC_LEVELS:
        raise ValidationError(
            "Error correction harus salah satu dari: " + ", ".join(ECC_LEVELS)
        )
    hex_to_rgb(design.fg_color)
    hex_to_rgb(design.bg_color)
    contrast = low_contrast_warning(design.fg_color, design.bg_color)
    if contrast:
        warnings.append(contrast)
    if design.logo_path is not None:
        if not isinstance(design.logo_fraction, (int, float)) or not (
            0.0 < design.logo_fraction <= MAX_LOGO_FRACTION
        ):
            raise ValidationError(
                f"Ukuran logo harus antara 0 dan {MAX_LOGO_FRACTION:.0%} dari lebar QR."
            )
        warnings.append(
            "Logo menutupi sebagian modul QR. QR berlogo TIDAK dijamin tetap dapat "
            "dipindai; semakin besar logo, semakin besar risiko keterbacaan."
        )
    return warnings


def _qr_image(data: str, design: QrDesign) -> "PilImage":
    from qrcode.image.pil import PilImage

    ec = {
        "L": qr_constants.ERROR_CORRECT_L,
        "M": qr_constants.ERROR_CORRECT_M,
        "Q": qr_constants.ERROR_CORRECT_Q,
        "H": qr_constants.ERROR_CORRECT_H,
    }[design.error_correction]
    qr = qrcode.QRCode(
        version=None,
        error_correction=ec,
        box_size=design.box_size,
        border=design.border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(
        image_factory=PilImage,
        fill_color=design.fg_color,
        back_color=design.bg_color,
    )


def build_qr_image(data: str, design: QrDesign) -> Tuple[object, List[str]]:
    """Build a Pillow image for ``data`` under ``design`` and return (image, warnings).

    The payload is used exactly as given (never truncated). ``DataOverflowError``
    is translated into a clear ``ValidationError`` so the user can shorten the
    text or lower the error-correction level.
    """
    from PIL import Image

    text = data if isinstance(data, str) else ""
    if not text.strip():
        raise ValidationError("Isi data QR tidak boleh kosong.")
    warnings = validate_design(design)
    try:
        img = _qr_image(text, design)
    except (DataOverflowError, ValueError):
        raise ValidationError(
            "Data terlalu panjang untuk QR Code pada pengaturan ini. "
            "Perpendek teks atau kurangi level error correction."
        )

    if design.logo_path is not None:
        logo_p = Path(design.logo_path)
        vr = validate_input_file(logo_p)
        if not vr.valid:
            raise ValidationError(vr.errors[0] if vr.errors else "Logo tidak valid.")
        try:
            logo = Image.open(logo_p)
            logo.load()
        except Exception:
            raise ValidationError("Logo tidak dapat dibaca sebagai gambar.")
        w, h = logo.size
        if w <= 0 or h <= 0:
            raise ValidationError("Gambar logo invalid.")
        if w * h > get_config().max_image_pixels:
            raise ValidationError(
                f"Gambar logo terlalu besar (batas {get_config().max_image_pixels} piksel)."
            )
        logo = logo.convert("RGBA")
        target_w = max(1, int(img.size[0] * design.logo_fraction))
        ratio = target_w / float(w)
        target_h = max(1, int(h * ratio))
        logo = logo.resize((target_w, target_h), Image.LANCZOS)
        paste_xy = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
        img = img.convert("RGBA")
        img.paste(logo, paste_xy, logo)
    return img, warnings


def render_qr_png(
    data: str,
    output_dir: str | Path,
    design: QrDesign | None = None,
    output_name: str | None = None,
) -> QrOutput:
    """Generate a QR PNG for ``data`` and save it to ``output_dir``.

    The written file is reopened (Pillow) for validation before the atomic rename.
    """
    design = design or QrDesign()
    img, warnings = build_qr_image(data, design)
    buf = io.BytesIO()
    fmt = "PNG"
    img.save(buf, format=fmt)
    buf.seek(0)
    data_bytes = buf.getvalue()

    name = (output_name or "qrcode").strip() or "qrcode"
    if not name.lower().endswith(".png"):
        name += ".png"
    out = safe_output_path(output_dir, name)

    def verify(tmp: Path) -> None:
        from PIL import Image

        with Image.open(tmp) as check:
            check.load()
            if check.size[0] <= 0 or check.size[1] <= 0:
                raise ValidationError("Gambar hasil kosong.")

    write_verified_content(data_bytes, out, ".png", verify)
    return QrOutput(output=out, fmt=fmt, warnings=warnings)


def render_qr_svg(
    data: str,
    output_dir: str | Path,
    design: QrDesign | None = None,
    output_name: str | None = None,
) -> QrOutput:
    """Generate an SVG QR and save it to ``output_dir``.

    Logo is NOT embedded into SVG (vector output cannot carry the raster logo
    without turning into a PNG-like file). A clear error is raised instead of a
    silent drop. The SVG is parsed to validate structure before the rename.
    """
    from qrcode.image.svg import SvgPathImage

    design = design or QrDesign()
    if design.logo_path is not None:
        raise ValidationError(
            "Logo tidak didukung pada ekspor SVG. Gunakan ekspor PNG untuk QR berlogo."
        )
    warnings = validate_design(design)
    text = data if isinstance(data, str) else ""
    if not text.strip():
        raise ValidationError("Isi data QR tidak boleh kosong.")
    ec = {
        "L": qr_constants.ERROR_CORRECT_L,
        "M": qr_constants.ERROR_CORRECT_M,
        "Q": qr_constants.ERROR_CORRECT_Q,
        "H": qr_constants.ERROR_CORRECT_H,
    }[design.error_correction]
    qr = qrcode.QRCode(
        version=None,
        error_correction=ec,
        box_size=design.box_size,
        border=design.border,
    )
    qr.add_data(text)
    try:
        qr.make(fit=True)
        svg_img = qr.make_image(
            image_factory=SvgPathImage,
            fill_color=design.fg_color,
            back_color=design.bg_color,
        )
        svg_bytes = svg_img.to_string()
    except (DataOverflowError, ValueError):
        raise ValidationError(
            "Data terlalu panjang untuk QR Code pada pengaturan ini. "
            "Perpendek teks atau kurangi level error correction."
        )

    name = (output_name or "qrcode").strip() or "qrcode"
    if not name.lower().endswith(".svg"):
        name += ".svg"
    out = safe_output_path(output_dir, name)

    def verify(tmp: Path) -> None:
        import xml.etree.ElementTree as ET

        try:
            root = ET.parse(tmp).getroot()
        except Exception:
            raise ValidationError("SVG tidak dapat diuraikan.")
        tag = root.tag.lower()
        if not tag.endswith("svg"):
            raise ValidationError("Struktur SVG tidak sesuai.")
        paths = [n for n in root.iter() if str(n.tag).lower().endswith("path")]
        if not paths:
            raise ValidationError("SVG hasil tidak memuat bentuk QR (path).")
        content = tmp.read_text(encoding="utf-8")
        if design.fg_color.upper() not in content.upper():
            raise ValidationError("Warna hasil tidak diterapkan pada SVG.")

    write_verified_content(svg_bytes, out, ".svg", verify)
    return QrOutput(output=out, fmt="SVG", warnings=warnings)