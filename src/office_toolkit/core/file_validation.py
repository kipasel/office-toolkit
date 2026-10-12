from pathlib import Path
from typing import List, Tuple

from .errors import ValidationError


class FileValidationResult:
    def __init__(self, valid: bool, errors: List[str]):
        self.valid = valid
        self.errors = errors

    def raise_if_invalid(self) -> None:
        if not self.valid:
            raise ValidationError("; ".join(self.errors))


def _is_illegal_name(name: str) -> bool:
    illegal = {'<', '>', ':', '"', '|', '?', '*'}
    if name in ('.', '..'):
        return True
    for c in illegal:
        if c in name:
            return True
    if len(name) > 255:
        return True
    return False


def validate_input_file(path: str | Path) -> FileValidationResult:
    errors: List[str] = []
    p = Path(path)
    if not p.exists():
        errors.append(f"File tidak ditemukan: {p}")
    elif not p.is_file():
        errors.append(f"Bukan file: {p}")
    elif p.stat().st_size == 0:
        errors.append(f"File kosong: {p}")
    else:
        try:
            with open(p, 'rb'):
                pass
        except PermissionError:
            errors.append(f"Tidak bisa membaca file: {p}")
        except OSError as e:
            errors.append(f"Error membaca file {p}: {e}")
    try:
        if _is_illegal_name(p.name):
            errors.append(f"Nama file tidak valid: {p.name}")
    except Exception:
        pass
    return FileValidationResult(len(errors) == 0, errors)


def validate_output_dir(path: str | Path) -> FileValidationResult:
    errors: List[str] = []
    p = Path(path)
    if not p.exists():
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Tidak bisa membuat folder output {p}: {e}")
    if not errors and not p.is_dir():
        errors.append(f"Bukan folder: {p}")
    if not errors:
        try:
            test = p / ".office_toolkit_write_test.tmp"
            test.touch(exist_ok=False)
            test.unlink(missing_ok=True)
        except Exception as e:
            errors.append(f"Tidak bisa menulis ke folder output {p}: {e}")
    return FileValidationResult(len(errors) == 0, errors)


def ensure_no_conflict(target: Path, allow_overwrite: bool = False) -> FileValidationResult:
    errors: List[str] = []
    if target.exists() and not allow_overwrite:
        errors.append(f"File sudah ada dan tidak diizinkan menimpa: {target}")
    return FileValidationResult(len(errors) == 0, errors)


def is_safe_path(base: Path, candidate: Path) -> bool:
    try:
        base_r = base.resolve()
        cand_r = candidate.resolve()
        return cand_r.is_relative_to(base_r)
    except Exception:
        return False
