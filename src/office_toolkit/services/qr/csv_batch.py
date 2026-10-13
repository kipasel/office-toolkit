"""CSV batch QR generation (Phase 5, Modul C - C5).

Reads a local CSV (UTF-8 with or without BOM), validates the header, and
generates one QR per data row into an output folder. One failing row does not
stop the batch. Filenames are sanitized against illegal Windows characters,
path traversal is prevented, and duplicates get an alternative name instead of
silent overwrite. A progress callback (row index, total) reports actual work.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from office_toolkit.core.config import get_config
from office_toolkit.core.errors import ResourceLimitError, ValidationError
from office_toolkit.core.output_manager import OutputManager

from .common import validate_table_file
from .generator import QrDesign, render_qr_png, render_qr_svg

SUPPORTED_FORMATS = ("png", "svg")


@dataclass
class CsvHeaderInfo:
    """Validated header names in file order."""

    headers: List[str]


@dataclass
class BatchResult:
    """Summary of a CSV batch run (succeeded / failed / skipped rows)."""

    output_dir: Path
    fmt: str
    succeeded: List[Path] = field(default_factory=list)
    failed: List[Tuple[int, str]] = field(default_factory=list)
    skipped_rows: int = 0
    total_rows: int = 0


def read_csv_rows(path: str | Path) -> Tuple[List[str], list, List[int]]:
    """Read ``path`` as UTF-8 (with or without BOM) using the csv module.

    Returns (header, data_rows, file_line_numbers). The header is the first
    non-empty row. Fully-blank rows are dropped and not part of ``data_rows``;
    ``file_line_numbers`` carries the original 1-based file line of each row so
    errors can point at the actual line.
    """
    p = validate_table_file(path)
    try:
        with open(p, "r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.reader(fh)
            lines = list(reader)
    except UnicodeDecodeError:
        raise ValidationError(
            "CSV tidak dapat dibaca sebagai UTF-8. Simpan file sebagai UTF-8 "
            "(dengan atau tanpa BOM) lalu coba lagi."
        )
    except csv.Error as e:
        raise ValidationError(f"CSV tidak valid: {e}")
    except OSError as e:
        raise ValidationError(f"CSV tidak dapat dibaca: {e}")

    rows: List[list] = []
    line_numbers: List[int] = []
    header: Optional[List[str]] = None
    header_line: int = 0
    for i, raw in enumerate(lines, start=1):
        row = [("" if c is None else str(c)).strip() for c in raw]
        if not row or all(not c for c in row):
            continue
        if header is None:
            header = row
            header_line = i
            continue
        rows.append(raw)
        line_numbers.append(i)

    if header_line != 1:
        raise ValidationError("Header (baris pertama) tidak boleh kosong.")
    if header is None:
        raise ValidationError("CSV kosong: tidak ada header.")
    dupes = [h for h in header if header.count(h) > 1]
    if dupes:
        raise ValidationError(f"Header mengandung nama kolom duplikat: {sorted(set(dupes))}.")
    if any(not h for h in header):
        raise ValidationError("Header mengandung nama kolom kosong.")
    max_rows = get_config().max_csv_batch_rows
    if len(rows) > max_rows:
        raise ResourceLimitError(
            f"Jumlah baris data ({len(rows)}) melebihi batas {max_rows} baris."
        )
    return header, rows, line_numbers


def preview_csv(
    path: str | Path, max_preview: int = 5
) -> Tuple[List[str], List[list]]:
    """Return (header, first data rows) without loading the whole file.

    Used by the UI to populate column pickers and show a short preview.
    Fully-blank rows are skipped. Errors mirror ``read_csv_rows``.
    """
    p = validate_table_file(path)
    try:
        with open(p, "r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.reader(fh)
            header: Optional[List[str]] = None
            preview: List[list] = []
            for raw in reader:
                row = [("" if c is None else str(c)) for c in raw]
                if not row or all(not c.strip() for c in row):
                    continue
                if header is None:
                    header = [c.strip() for c in row]
                    continue
                preview.append(row)
                if len(preview) >= max_preview:
                    break
    except UnicodeDecodeError:
        raise ValidationError(
            "CSV tidak dapat dibaca sebagai UTF-8. Simpan file sebagai UTF-8 "
            "(dengan atau tanpa BOM) lalu coba lagi."
        )
    except csv.Error as e:
        raise ValidationError(f"CSV tidak valid: {e}")
    except OSError as e:
        raise ValidationError(f"CSV tidak dapat dibaca: {e}")

    if header is None:
        raise ValidationError("CSV kosong: tidak ada header.")
    dupes = [h for h in header if header.count(h) > 1]
    if dupes:
        raise ValidationError(f"Header mengandung nama kolom duplikat: {sorted(set(dupes))}.")
    if any(not h for h in header):
        raise ValidationError("Header mengandung nama kolom kosong.")
    return header, preview


def _cell_value(row: list, index: int) -> str:
    if index < 0 or index >= len(row):
        return ""
    v = row[index]
    return "" if v is None else str(v)


def _sanitize_stem(name: str) -> str:
    sanitized = OutputManager._sanitize_filename(name)
    stem = Path(sanitized).stem if sanitized else ""
    return (stem or "").strip()


def process_csv_batch(
    csv_path: str | Path,
    output_dir: str | Path,
    content_column: str,
    filename_column: Optional[str] = None,
    fmt: str = "png",
    design: Optional[QrDesign] = None,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> BatchResult:
    """Generate one QR per data row into ``output_dir``.

    ``progress_cb(current, total)`` is called once per processed row. Errors are
    collected per row (1-based file line) and the batch continues unless the
    input itself is invalid. Nothing is overwritten silently.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValidationError(
            f"Format tidak didukung: {fmt}. Gunakan: {', '.join(SUPPORTED_FORMATS)}."
        )
    design = design or QrDesign()
    if design.logo_path is not None and fmt == "svg":
        raise ValidationError("Logo tidak didukung untuk ekspor SVG batch.")
    if not content_column or not content_column.strip():
        raise ValidationError("Pilih kolom yang berisi data QR.")

    header, rows, line_numbers = read_csv_rows(csv_path)
    if content_column not in header:
        raise ValidationError(
            f"Kolom konten '{content_column}' tidak ada di header: {header}."
        )
    content_idx = header.index(content_column)
    filename_idx: Optional[int] = None
    if filename_column:
        if filename_column not in header:
            raise ValidationError(
                f"Kolom nama file '{filename_column}' tidak ada di header: {header}."
            )
        filename_idx = header.index(filename_column)

    out_dir = Path(output_dir)
    result = BatchResult(output_dir=out_dir, fmt=fmt, total_rows=len(rows))
    if not rows:
        return result

    seq = 0
    for idx, (raw_row, line) in enumerate(zip(rows, line_numbers), start=1):
        if progress_cb is not None:
            progress_cb(idx, len(rows))
        content = _cell_value(raw_row, content_idx)
        if not content.strip():
            result.failed.append((line, "Kolom konten kosong."))
            continue

        raw_name = ""
        if filename_idx is not None:
            raw_name = _cell_value(raw_row, filename_idx).strip()
        stem = _sanitize_stem(raw_name) if raw_name else ""
        if not stem:
            seq += 1
            stem = f"qr_{seq:04d}"
        name = f"{stem}.{fmt}"

        try:
            if fmt == "svg":
                res = render_qr_svg(content, out_dir, design=design, output_name=name)
            else:
                res = render_qr_png(content, out_dir, design=design, output_name=name)
            result.succeeded.append(res.output)
        except ValidationError as e:
            result.failed.append((line, str(e)))
        except Exception as e:
            result.failed.append((line, f"Gagal memproses baris: {e}"))

    result.skipped_rows = len(rows) - len(result.succeeded) - len(result.failed)
    return result