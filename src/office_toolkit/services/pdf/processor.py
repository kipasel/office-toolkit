"""Core PDF page-management operations (info, merge, split, extract, reorder, rotate).

All operations run locally using PyMuPDF. No network access. Source files are never
modified: every operation writes to a new file through the OutputManager, using a
temporary file that is atomically renamed only after the result is verified.

Known limitations (documented, not hidden):
- Merge/extract/reorder/split build a new document with ``insert_pdf``; the document
  outline (bookmarks), XMP metadata, and some interactive form structures are not
  guaranteed to be preserved.
- Rotate is applied to a copy of the source document, so metadata and outline are
  preserved while page rotation is changed.
- Encrypted PDFs are rejected (``PasswordError``); passwords are never guessed or
  cracked, and never logged.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

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
_RANGE_RE = re.compile(r"^\s*(\d+)\s*(?:-\s*(\d+)\s*)?$")


@dataclass
class PdfInfoResult:
    """Read-only information about a PDF file."""

    path: Path
    size_bytes: int
    page_count: Optional[int]
    encrypted: bool
    needs_password: bool
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    producer: Optional[str] = None
    creator: Optional[str] = None
    creation_date: Optional[str] = None
    mod_date: Optional[str] = None
    page_size: Optional[Tuple[float, float]] = None
    uniform_page_size: Optional[bool] = None
    metadata_error: Optional[str] = None


@dataclass
class MergeResult:
    inputs: List[Path]
    output: Path
    page_count: int
    input_page_counts: List[int]

    @property
    def total_input_pages(self) -> int:
        return sum(self.input_page_counts)


@dataclass
class SplitFile:
    output: Path
    start: int
    end: int

    @property
    def page_count(self) -> int:
        return self.end - self.start + 1


@dataclass
class SplitResult:
    input: Path
    outputs: List[SplitFile]
    source_page_count: int


@dataclass
class ExtractResult:
    input: Path
    output: Path
    requested_pages: List[int]
    page_count: int


@dataclass
class ReorderResult:
    input: Path
    output: Path
    order: List[int]
    page_count: int


@dataclass
class RotateResult:
    input: Path
    output: Path
    pages: List[int]
    angle: int
    page_count: int


def _check_size(path: Path) -> None:
    limit = get_config().max_input_mb * _MB
    try:
        size = path.stat().st_size
    except OSError as e:  # pragma: no cover - defensive
        raise ValidationError(f"Tidak bisa membaca ukuran file: {e}")
    if size > limit:
        raise ResourceLimitError(
            f"Ukuran file melebihi batas {get_config().max_input_mb} MB: {path.name}"
        )


def _open_checked(path: Path, *, allow_encrypted: bool = False) -> pymupdf.Document:
    """Validate and open a PDF, translating library errors into toolkit errors."""
    v = validate_input_file(path)
    if not v.valid:
        raise ValidationError(v.errors[0] if v.errors else f"File tidak valid: {path}")
    _check_size(path)
    try:
        doc = pymupdf.open(str(path))
    except pymupdf.EmptyFileError:
        raise DecodeError(f"File PDF kosong: {path.name}")
    except pymupdf.FileDataError:
        raise DecodeError(f"Bukan PDF valid atau file rusak: {path.name}")
    except RuntimeError as e:
        raise DecodeError(f"Gagal membuka PDF {path.name}: {e}")

    if (getattr(doc, "needs_pass", False) or doc.is_encrypted) and not allow_encrypted:
        doc.close()
        raise PasswordError(
            f"PDF terenkripsi memerlukan kata sandi dan tidak dapat diproses: {path.name}"
        )
    return doc


def get_pdf_info(path: str | Path) -> PdfInfoResult:
    """Return metadata and basic dimensions for a PDF (read-only)."""
    p = Path(path)
    v = validate_input_file(p)
    if not v.valid:
        raise ValidationError(v.errors[0] if v.errors else f"File tidak valid: {p}")
    _check_size(p)
    size = p.stat().st_size

    try:
        doc = pymupdf.open(str(p))
    except pymupdf.EmptyFileError:
        raise DecodeError(f"File PDF kosong: {p.name}")
    except pymupdf.FileDataError:
        raise DecodeError(f"Bukan PDF valid atau file rusak: {p.name}")
    except RuntimeError as e:
        raise DecodeError(f"Gagal membuka PDF {p.name}: {e}")

    encrypted = bool(doc.is_encrypted)
    needs_pass = bool(getattr(doc, "needs_pass", False))
    result = PdfInfoResult(
        path=p,
        size_bytes=size,
        page_count=None,
        encrypted=encrypted,
        needs_password=needs_pass,
    )

    if needs_pass:
        result.metadata_error = "Metadata tidak dapat dibaca: PDF terenkripsi."
        doc.close()
        return result

    try:
        result.page_count = doc.page_count
    except Exception as e:  # pragma: no cover - defensive
        result.metadata_error = f"Gagal membaca jumlah halaman: {e}"

    if result.page_count:
        try:
            sizes: List[Tuple[float, float]] = []
            for i in range(result.page_count):
                r = doc[i].rect
                sizes.append((round(r.width, 2), round(r.height, 2)))
            result.page_size = sizes[0]
            result.uniform_page_size = len(set(sizes)) == 1
        except Exception as e:
            result.metadata_error = f"Gagal membaca ukuran halaman: {e}"

    try:
        md = doc.metadata or {}
    except Exception as e:
        result.metadata_error = f"Gagal membaca metadata: {e}"
        md = {}

    def _clean(key: str) -> Optional[str]:
        val = md.get(key)
        if val is None:
            return None
        val = str(val).strip()
        return val or None

    result.title = _clean("title")
    result.author = _clean("author")
    result.subject = _clean("subject")
    result.keywords = _clean("keywords")
    result.producer = _clean("producer")
    result.creator = _clean("creator")
    result.creation_date = _clean("creationDate")
    result.mod_date = _clean("modDate")

    doc.close()
    return result


def parse_page_ranges(spec: str, page_count: int) -> List[Tuple[int, int]]:
    """Parse a user range spec like ``1-3, 5, 7-9`` into 1-based inclusive ranges.

    Overlapping or adjacent ranges are allowed and returned in the given order.
    """
    if not spec or not spec.strip():
        raise ValidationError("Rentang halaman tidak boleh kosong.")
    if page_count <= 0:
        raise ValidationError("Dokumen tidak memiliki halaman.")
    ranges: List[Tuple[int, int]] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        m = _RANGE_RE.match(token)
        if not m:
            raise ValidationError(f"Format rentang tidak valid: '{token}' (contoh: 1-3, 5)")
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start
        if start < 1 or end < 1:
            raise ValidationError("Nomor halaman dimulai dari 1.")
        if start > end:
            raise ValidationError(f"Rentang terbalik tidak diizinkan: '{token}'.")
        if end > page_count:
            raise ValidationError(
                f"Halaman {end} di luar jangkauan (dokumen memiliki {page_count} halaman)."
            )
        ranges.append((start, end))
    if not ranges:
        raise ValidationError("Tidak ada rentang halaman yang valid.")
    return ranges


def parse_pages(spec: str, page_count: int) -> List[int]:
    """Parse a page spec (singles, ranges, duplicates) into an expanded 1-based list.

    Order is preserved as written; ranges are expanded in ascending order.
    Example: ``"3, 1, 5-7"`` -> ``[3, 1, 5, 6, 7]``.
    """
    return [n for start, end in parse_page_ranges(spec, page_count) for n in range(start, end + 1)]


def _save_verified(doc: pymupdf.Document, out_path: Path, expected_pages: int) -> None:
    """Save ``doc`` to ``out_path`` via a temporary file, then verify and rename."""
    om = OutputManager()
    tmp = om.write_temp_in_dir(out_path.parent, suffix=".pdf")
    try:
        try:
            doc.save(str(tmp), garbage=0, deflate=True)
        except Exception as e:
            raise OutputError(f"Gagal menyimpan hasil PDF: {e}")
        try:
            with pymupdf.open(str(tmp)) as check:
                actual = check.page_count
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


def merge_pdfs(
    inputs: Sequence[str | Path],
    output_dir: str | Path,
    output_name: Optional[str] = None,
) -> MergeResult:
    """Merge two or more PDFs into one, preserving the given order."""
    paths = [Path(p) for p in inputs]
    if len(paths) < 2:
        raise ValidationError("Merge memerlukan minimal dua file PDF.")
    for p in paths:
        if not p.exists():
            raise ValidationError(f"File tidak ditemukan: {p}")
    if len({str(p.resolve()) for p in paths}) != len(paths):
        raise ValidationError("File sumber duplikat tidak diizinkan untuk merge.")

    out_dir = Path(output_dir)
    om = OutputManager(default_dir=out_dir)
    name = output_name or "gabungan.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    out_path = om.safe_output_path(name, dir_path=out_dir, allow_overwrite=False)

    docs: List[pymupdf.Document] = []
    page_counts: List[int] = []
    out = pymupdf.open()
    try:
        for p in paths:
            src = _open_checked(p)
            docs.append(src)
            page_counts.append(src.page_count)
            try:
                out.insert_pdf(src, links=True, annots=True)
            except Exception as e:
                raise ProcessingError(f"Gagal menggabungkan {p.name}: {e}")
        expected = sum(page_counts)
        _save_verified(out, out_path, expected)
    finally:
        out.close()
        for d in docs:
            try:
                d.close()
            except Exception:
                pass

    return MergeResult(
        inputs=paths, output=out_path, page_count=expected, input_page_counts=page_counts
    )


def split_by_ranges(
    input_path: str | Path,
    ranges: Sequence[Tuple[int, int]],
    output_dir: str | Path,
    base_name: Optional[str] = None,
) -> SplitResult:
    """Split a PDF into one output file per 1-based inclusive range."""
    src_path = Path(input_path)
    src = _open_checked(src_path)
    out_dir = Path(output_dir)
    om = OutputManager(default_dir=out_dir)
    stem = base_name or src_path.stem
    total = src.page_count
    outputs: List[SplitFile] = []
    created: List[Path] = []
    try:
        if not ranges:
            raise ValidationError("Tidak ada rentang halaman.")
        for start, end in ranges:
            if start < 1 or end < 1 or start > end or end > total:
                raise ValidationError(f"Rentang tidak valid: {start}-{end}")
            label = f"{start}" if start == end else f"{start}-{end}"
            out_path = om.safe_output_path(
                f"{stem}_hal_{label}.pdf", dir_path=out_dir, allow_overwrite=False
            )
            new = pymupdf.open()
            try:
                new.insert_pdf(src, from_page=start - 1, to_page=end - 1, links=True, annots=True)
                _save_verified(new, out_path, end - start + 1)
            finally:
                new.close()
            created.append(out_path)
            outputs.append(SplitFile(output=out_path, start=start, end=end))
    except Exception:
        for p in created:
            om.cleanup(p)
        raise
    finally:
        src.close()
    return SplitResult(input=src_path, outputs=outputs, source_page_count=total)


def split_each_page(
    input_path: str | Path,
    output_dir: str | Path,
    base_name: Optional[str] = None,
) -> SplitResult:
    """Split a PDF so that every page becomes its own single-page PDF file."""
    src_path = Path(input_path)
    src = _open_checked(src_path)
    out_dir = Path(output_dir)
    om = OutputManager(default_dir=out_dir)
    stem = base_name or src_path.stem
    width = max(3, len(str(src.page_count)))
    total = src.page_count
    outputs: List[SplitFile] = []
    created: List[Path] = []
    try:
        for i in range(total):
            n = i + 1
            out_path = om.safe_output_path(
                f"{stem}_hal_{n:0{width}d}.pdf", dir_path=out_dir, allow_overwrite=False
            )
            new = pymupdf.open()
            try:
                new.insert_pdf(src, from_page=i, to_page=i, links=True, annots=True)
                _save_verified(new, out_path, 1)
            finally:
                new.close()
            created.append(out_path)
            outputs.append(SplitFile(output=out_path, start=n, end=n))
    except Exception:
        for p in created:
            om.cleanup(p)
        raise
    finally:
        src.close()
    return SplitResult(input=src_path, outputs=outputs, source_page_count=total)


def extract_pages(
    input_path: str | Path,
    pages: Sequence[int],
    output_dir: str | Path,
    output_name: Optional[str] = None,
) -> ExtractResult:
    """Create a new PDF containing only the selected pages, in the requested order.

    Duplicate page numbers are allowed and preserved in the given order.
    """
    src_path = Path(input_path)
    src = _open_checked(src_path)
    total = src.page_count
    if not pages:
        src.close()
        raise ValidationError("Tidak ada halaman yang dipilih.")
    for n in pages:
        if n < 1 or n > total:
            src.close()
            raise ValidationError(
                f"Halaman {n} di luar jangkauan (dokumen memiliki {total} halaman)."
            )
    out_dir = Path(output_dir)
    om = OutputManager(default_dir=out_dir)
    name = output_name or f"{src_path.stem}_ekstrak.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    out_path = om.safe_output_path(name, dir_path=out_dir, allow_overwrite=False)
    out = pymupdf.open()
    try:
        for n in pages:
            out.insert_pdf(src, from_page=n - 1, to_page=n - 1, links=True, annots=True)
        _save_verified(out, out_path, len(pages))
    finally:
        out.close()
        src.close()
    return ExtractResult(
        input=src_path, output=out_path, requested_pages=list(pages), page_count=len(pages)
    )


def reorder_pages(
    input_path: str | Path,
    order: Sequence[int],
    output_dir: str | Path,
    output_name: Optional[str] = None,
) -> ReorderResult:
    """Reorder pages. ``order`` must be a full permutation of 1..page_count."""
    src_path = Path(input_path)
    src = _open_checked(src_path)
    total = src.page_count
    if sorted(order) != list(range(1, total + 1)):
        src.close()
        raise ValidationError(
            f"Urutan harus memuat setiap halaman tepat sekali (1..{total})."
        )
    out_dir = Path(output_dir)
    om = OutputManager(default_dir=out_dir)
    name = output_name or f"{src_path.stem}_urut.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    out_path = om.safe_output_path(name, dir_path=out_dir, allow_overwrite=False)
    out = pymupdf.open()
    try:
        for n in order:
            out.insert_pdf(src, from_page=n - 1, to_page=n - 1, links=True, annots=True)
        _save_verified(out, out_path, total)
    finally:
        out.close()
        src.close()
    return ReorderResult(
        input=src_path, output=out_path, order=list(order), page_count=total
    )


def rotate_pages(
    input_path: str | Path,
    pages: Sequence[int],
    angle: int,
    output_dir: str | Path,
    output_name: Optional[str] = None,
) -> RotateResult:
    """Rotate the selected pages by 90, 180, or 270 degrees clockwise into a new file."""
    if angle not in (90, 180, 270):
        raise ValidationError("Sudut rotasi harus 90, 180, atau 270 derajat.")
    src_path = Path(input_path)
    src = _open_checked(src_path)
    total = src.page_count
    if not pages:
        src.close()
        raise ValidationError("Tidak ada halaman yang dipilih untuk diputar.")
    norm: List[int] = []
    for n in pages:
        if n < 1 or n > total:
            src.close()
            raise ValidationError(
                f"Halaman {n} di luar jangkauan (dokumen memiliki {total} halaman)."
            )
        norm.append(n)

    out_dir = Path(output_dir)
    om = OutputManager(default_dir=out_dir)
    name = output_name or f"{src_path.stem}_rotasi_{angle}.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    out_path = om.safe_output_path(name, dir_path=out_dir, allow_overwrite=False)

    try:
        for n in set(norm):
            page = src[n - 1]
            page.set_rotation((page.rotation + angle) % 360)
        _save_verified(src, out_path, total)
    except (ValidationError, PasswordError, ResourceLimitError, DecodeError, OutputError):
        raise
    except Exception as e:
        raise ProcessingError(f"Gagal memutar halaman: {e}")
    finally:
        src.close()

    return RotateResult(
        input=src_path, output=out_path, pages=norm, angle=angle, page_count=total
    )
