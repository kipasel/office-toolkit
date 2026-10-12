"""Synthetic PDF fixtures for tests (no real/personal documents)."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Tuple

import pymupdf

DEFAULT_SIZE: Tuple[float, float] = (200.0, 120.0)


def make_pdf(
    path: str | Path,
    labels: Sequence[str],
    size: Tuple[float, float] = DEFAULT_SIZE,
) -> Path:
    """Create a PDF where each page contains one text label (its identity)."""
    p = Path(path)
    doc = pymupdf.open()
    try:
        for label in labels:
            page = doc.new_page(width=size[0], height=size[1])
            page.insert_text((20, 40), str(label), fontsize=16)
        doc.save(str(p))
    finally:
        doc.close()
    return p


def make_encrypted_pdf(
    path: str | Path,
    user_pw: str = "rahasia",
    owner_pw: str = "pemilik",
    labels: Sequence[str] = ("S1", "S2"),
) -> Path:
    """Create a password-protected PDF using a known user password."""
    p = Path(path)
    doc = pymupdf.open()
    try:
        for label in labels:
            page = doc.new_page(width=DEFAULT_SIZE[0], height=DEFAULT_SIZE[1])
            page.insert_text((20, 40), str(label), fontsize=16)
        doc.save(
            str(p),
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw=owner_pw,
            user_pw=user_pw,
        )
    finally:
        doc.close()
    return p


def make_corrupt_pdf(path: str | Path) -> Path:
    """Create a file with a PDF-looking header but invalid body."""
    p = Path(path)
    p.write_bytes(b"%PDF-1.4\nnot a valid pdf body\x00\x01\x02")
    return p


def read_page_texts(path: str | Path) -> list[str]:
    """Return the text of each page in order (used to verify page identity)."""
    with pymupdf.open(str(path)) as doc:
        return [doc[i].get_text().strip() for i in range(doc.page_count)]


def page_count(path: str | Path) -> int:
    with pymupdf.open(str(path)) as doc:
        return doc.page_count
