"""Shared helpers for the QR services (Phase 5).

Offline building blocks used by generation, CSV batch, and decoding. Every
helper here validates input, enforces resource limits from ``AppConfig``, never
modifies source files, and never logs QR payloads or filenames with sensitive
content.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Tuple

from office_toolkit.core.config import get_config
from office_toolkit.core.errors import (
    DecodeError,
    OutputError,
    ResourceLimitError,
    ValidationError,
)
from office_toolkit.core.file_validation import validate_input_file
from office_toolkit.core.output_manager import OutputManager

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_MB = 1024 * 1024

MIN_CONTRAST_RATIO = 3.0


def check_input_size(path: Path) -> None:
    """Enforce the configured maximum input size for a single file."""
    limit = get_config().max_input_mb * _MB
    try:
        size = path.stat().st_size
    except OSError as e:  # pragma: no cover - defensive
        raise ValidationError(f"Tidak bisa membaca ukuran file: {e}")
    if size > limit:
        raise ResourceLimitError(
            f"Ukuran file melebihi batas {get_config().max_input_mb} MB: {path.name}"
        )


def validate_table_file(path: str | Path) -> Path:
    """Validate an input file that must exist, be readable, and be within limits."""
    p = Path(path)
    v = validate_input_file(p)
    if not v.valid:
        raise ValidationError(v.errors[0] if v.errors else f"File tidak valid: {p}")
    check_input_size(p)
    return p


def hex_to_rgb(value: str) -> Tuple[int, int, int]:
    """Parse ``#RRGGBB`` into an (r, g, b) tuple; raise ValidationError otherwise."""
    v = (value or "").strip()
    m = _HEX_RE.match(v)
    if not m:
        raise ValidationError("Format warna harus #RRGGBB (contoh: #000000, #FFC000).")
    h = m.group(0)[1:]
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _luminance(rgb: Tuple[int, int, int]) -> float:
    def lin(v: float) -> float:
        if v <= 0.03928:
            return v / 12.92
        return ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (c / 255.0 for c in rgb)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(fg: Tuple[int, int, int], bg: Tuple[int, int, int]) -> float:
    """WCAG-style contrast ratio between two RGB colours."""
    l1 = _luminance(fg)
    l2 = _luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def low_contrast_warning(fg: str, bg: str) -> Optional[str]:
    """Return a warning string when fg/bg contrast is potentially too low."""
    try:
        ratio = contrast_ratio(hex_to_rgb(fg), hex_to_rgb(bg))
    except ValidationError:
        return None
    if ratio < MIN_CONTRAST_RATIO:
        return (
            f"Kontras warna rendah (rasio {ratio:.1f}:1, disarankan minimal "
            f"{MIN_CONTRAST_RATIO:.1f}:1). QR dapat menjadi sulit dipindai."
        )
    return None


def safe_output_path(output_dir: str | Path, name: str, allow_overwrite: bool = False) -> Path:
    """Return a conflict-safe destination path inside ``output_dir``."""
    d = Path(output_dir)
    om = OutputManager(default_dir=d)
    return om.safe_output_path(name, dir_path=d, allow_overwrite=allow_overwrite)


def write_verified_content(
    data: bytes, out_path: Path, suffix: str, verify: callable
) -> Path:
    """Write ``data`` to a temp file next to the target, verify it, then rename.

    ``verify`` receives the temporary ``Path`` and must raise on invalid content.
    Any leftover temporary file is cleaned up on failure.
    """
    om = OutputManager()
    tmp = om.write_temp_in_dir(out_path.parent, suffix=suffix)
    try:
        try:
            tmp.write_bytes(data)
        except OSError as e:
            raise OutputError(f"Gagal menulis file hasil: {e}")
        try:
            verify(tmp)
        except OutputError:
            raise
        except Exception as e:
            raise OutputError(f"Hasil tidak dapat dibuka kembali: {e}")
        try:
            import os

            os.replace(str(tmp), str(out_path))
        except OSError as e:
            raise OutputError(f"Gagal menulis file hasil: {e}")
    finally:
        om.cleanup(tmp)
    return out_path