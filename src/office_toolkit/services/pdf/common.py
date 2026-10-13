"""Shared helpers for the advanced PDF services (Phase 4).

These are read/process/write building blocks shared by feature modules such as
compression, rendering, image construction, editing, annotation, and security.
Every function here is offline, validates input, and never modifies the source
file. Passwords are never logged or embedded in messages or filenames.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Sequence, Union

import pymupdf

from office_toolkit.core.config import get_config
from office_toolkit.core.errors import (
    DecodeError,
    OutputError,
    PasswordError,
    ProcessingError,
    ResourceLimitError,
    ValidationError,
)
from office_toolkit.core.file_validation import validate_input_file
from office_toolkit.core.output_manager import OutputManager

_MB = 1024 * 1024


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


def _open_doc(**kwargs) -> pymupdf.Document:
    """Open a PDF via PyMuPDF, mapping low-level errors to toolkit errors."""
    try:
        return pymupdf.open(**kwargs)
    except pymupdf.EmptyFileError:
        raise DecodeError("File PDF kosong.")
    except pymupdf.FileDataError:
        raise DecodeError("Bukan PDF valid atau file rusak.")
    except RuntimeError as e:
        raise DecodeError(f"Gagal membuka PDF: {e}")


def open_pdf(path: str | Path, password: Optional[str] = None) -> pymupdf.Document:
    """Validate a PDF and open it, translating library errors into toolkit errors.

    An encrypted document is accepted only when a password is provided and the
    authentication succeeds. Encrypted sources are re-opened from an in-memory
    copy before authentication so that MuPDF's per-path caches can never serve a
    stale (not fully decrypted) document. The password is never included in
    messages or filenames.
    """
    p = Path(path)
    v = validate_input_file(p)
    if not v.valid:
        raise ValidationError(v.errors[0] if v.errors else f"File tidak valid: {p}")
    check_input_size(p)
    doc = _open_doc(filename=str(p))

    if getattr(doc, "needs_pass", False) or doc.is_encrypted:
        if not password:
            doc.close()
            raise PasswordError(
                f"PDF terenkripsi memerlukan kata sandi dan tidak dapat diproses: {p.name}"
            )
        doc.close()
        doc = _open_doc(stream=p.read_bytes(), filetype="pdf")
        try:
            authenticated = doc.authenticate(password)
        except Exception:
            authenticated = 0
        if not authenticated:
            doc.close()
            raise PasswordError("Kata sandi salah; PDF tidak dapat dibuka.")
    return doc


def write_verified_pdf(
    doc: pymupdf.Document,
    out_path: Path,
    expected_pages: int,
    *,
    open_password: Optional[str] = None,
    expect_encrypted: Optional[bool] = None,
    **save_kwargs,
) -> None:
    """Save ``doc`` to a temporary file, verify it reopens, then atomically rename.

    ``open_password`` authenticates an encrypted result before page counting.
    ``expect_encrypted`` asserts the encryption state of the written file.
    """
    om = OutputManager()
    tmp = om.write_temp_in_dir(out_path.parent, suffix=".pdf")
    try:
        try:
            doc.save(str(tmp), **save_kwargs)
        except Exception as e:
            raise OutputError(f"Gagal menyimpan hasil PDF: {e}")
        try:
            with pymupdf.open(str(tmp)) as check:
                if expect_encrypted is not None:
                    is_enc = bool(getattr(check, "needs_pass", False) or check.is_encrypted)
                    if is_enc != expect_encrypted:
                        raise OutputError(
                            "Verifikasi gagal: status enkripsi hasil tidak sesuai harapan."
                        )
                if getattr(check, "needs_pass", False) and open_password is not None:
                    check.authenticate(open_password)
                actual = check.page_count
        except OutputError:
            raise
        except Exception as e:
            raise OutputError(f"Hasil PDF tidak dapat dibuka kembali: {e}")
        if actual != expected_pages:
            raise OutputError(
                f"Verifikasi gagal: hasil berisi {actual} halaman, diharapkan {expected_pages}."
            )
        try:
            os.replace(str(tmp), str(out_path))
        except OSError as e:
            raise OutputError(f"Gagal menulis file hasil: {e}")
    finally:
        om.cleanup(tmp)


def write_image_bytes(data: bytes, out_path: Path, ext: str) -> None:
    """Write image bytes to a temp file next to the target, verify, then rename."""
    om = OutputManager()
    tmp = om.write_temp_in_dir(out_path.parent, suffix=ext)
    try:
        try:
            tmp.write_bytes(data)
        except OSError as e:
            raise OutputError(f"Gagal menulis gambar hasil: {e}")
        try:
            from PIL import Image

            with Image.open(tmp) as im:
                im.load()
        except Exception as e:
            raise OutputError(f"Gambar hasil tidak dapat dibuka kembali: {e}")
        try:
            os.replace(str(tmp), str(out_path))
        except OSError as e:
            raise OutputError(f"Gagal menulis file hasil: {e}")
    finally:
        om.cleanup(tmp)


def safe_output_path(
    output_dir: str | Path, name: str, allow_overwrite: bool = False
) -> Path:
    """Return a conflict-safe destination path inside ``output_dir``."""
    d = Path(output_dir)
    om = OutputManager(default_dir=d)
    return om.safe_output_path(name, dir_path=d, allow_overwrite=allow_overwrite)


def resolve_pages(pages: Union[str, Sequence[int]], page_count: int) -> List[int]:
    """Expand a page spec or validate an explicit 1-based page list."""
    if isinstance(pages, str):
        if page_count <= 0:
            raise ValidationError("Dokumen tidak memiliki halaman.")
        from . import processor

        return processor.parse_pages(pages, page_count)
    sel = list(pages)
    if not sel:
        raise ValidationError("Tidak ada halaman yang dipilih.")
    for n in sel:
        if isinstance(n, bool) or not isinstance(n, int):
            raise ValidationError("Nomor halaman harus bilangan bulat.")
        if n < 1 or n > page_count:
            raise ValidationError(
                f"Halaman {n} di luar jangkauan (dokumen memiliki {page_count} halaman)."
            )
    return sel


def savings_percent(input_size: int, output_size: int) -> float:
    """Return (input - output) / input * 100. Negative means output is larger."""
    if input_size <= 0:
        return 0.0
    return (input_size - output_size) / input_size * 100.0


def check_render_limits(page_count: int, dpi: int) -> None:
    """Enforce documented DPI and page-count limits for rendering."""
    cfg = get_config()
    if dpi < cfg.pdf_render_dpi_min or dpi > cfg.pdf_render_dpi_max:
        raise ValidationError(
            f"DPI harus antara {cfg.pdf_render_dpi_min} dan {cfg.pdf_render_dpi_max}."
        )
    if page_count > cfg.max_pdf_pages_render:
        raise ResourceLimitError(
            f"Jumlah halaman melebihi batas {cfg.max_pdf_pages_render} halaman untuk diproses."
        )