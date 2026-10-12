import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from .errors import OutputError, ValidationError
from .file_validation import ensure_no_conflict, validate_output_dir


class OutputManager:
    def __init__(self, default_dir: Optional[Path] = None):
        self.default_dir = Path(default_dir) if default_dir else Path.cwd()

    def safe_output_path(self, filename: str, dir_path: Optional[Path] = None, allow_overwrite: bool = False) -> Path:
        out_dir = Path(dir_path) if dir_path else self.default_dir
        v = validate_output_dir(out_dir)
        if not v.valid:
            raise ValidationError(v.errors[0] if v.errors else "Folder output tidak valid")
        fname = self._sanitize_filename(filename)
        target = out_dir / fname
        c = ensure_no_conflict(target, allow_overwrite=allow_overwrite)
        if not c.valid:
            # generate alternative name
            alt = self._alternative_name(target)
            alt_c = ensure_no_conflict(alt, allow_overwrite=allow_overwrite)
            if not alt_c.valid:
                raise OutputError(alt_c.errors[0] if alt_c.errors else "Konflik nama file")
            target = alt
        return target

    def write_temp_in_dir(self, dir_path: Path, suffix: str = ".tmp") -> Path:
        v = validate_output_dir(dir_path)
        if not v.valid:
            raise ValidationError(v.errors[0] if v.errors else "Folder output tidak valid")
        fd, path = tempfile.mkstemp(dir=str(dir_path), suffix=suffix, prefix="otk_")
        try:
            os.close(fd)
        except Exception:
            pass
        return Path(path)

    @staticmethod
    def cleanup(path: Optional[Path]) -> None:
        if path and path.exists():
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        illegal = '<>:"/\\|?*'
        for c in illegal:
            name = name.replace(c, '_')
        if name in ('.', '..'):
            name = '_'
        if len(name) > 255:
            root, ext = os.path.splitext(name)
            name = root[:200] + ext
        return name

    @staticmethod
    def _alternative_name(target: Path) -> Path:
        root = target.stem
        ext = target.suffix
        i = 1
        while True:
            cand = target.parent / f"{root}_{i}{ext}"
            if not cand.exists():
                return cand
            i += 1
            if i > 9999:
                raise OutputError("Tidak bisa membuat nama alternatif unik")
