"""Synthetic QR and CSV fixtures for tests (no real/personal data)."""

from __future__ import annotations

from pathlib import Path

import qrcode


def make_qr_image(
    path: str | Path,
    data: str,
    box_size: int = 10,
    border: int = 4,
    fill: str = "#000000",
    back: str = "#FFFFFF",
) -> Path:
    """Write a synthetic QR code PNG that decodes back to ``data``."""
    p = Path(path)
    qr = qrcode.QRCode(
        version=None, error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size, border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr.make_image(fill_color=fill, back_color=back).save(str(p))
    return p


def make_plain_image(path: str | Path, size: int = 120) -> Path:
    """Write a solid-colour PNG that contains no QR code."""
    from PIL import Image

    p = Path(path)
    Image.new("RGB", (size, size), (240, 240, 240)).save(str(p))
    return p


def make_corrupt_image(path: str | Path) -> Path:
    """Write a file that is not a decodable image."""
    p = Path(path)
    p.write_bytes(b"\x89PNG-not-really-a-png-\x00\x01\x02broken")
    return p


def make_logo(
    path: str | Path,
    size: int = 64,
    transparent: bool = False,
    color: tuple = (200, 40, 40),
) -> Path:
    """Write a small RGBA logo (square)."""
    from PIL import Image, ImageDraw

    p = Path(path)
    img = Image.new("RGBA", (size, size), (*color, 0 if transparent else 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill=(*color, 255))
    img.save(str(p))
    return p


def make_csv(
    path: str | Path,
    headers: list,
    rows: list,
    bom: bool = False,
) -> Path:
    """Write a CSV with the standard library (UTF-8, optional BOM)."""
    import csv

    p = Path(path)
    enc = "utf-8-sig" if bom else "utf-8"
    with open(p, "w", encoding=enc, newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
    return p