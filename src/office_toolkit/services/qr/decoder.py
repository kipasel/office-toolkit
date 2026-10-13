"""QR decoding from local images (Phase 5, Modul C - C6).

Uses ``cv2.QRCodeDetector`` (opencv-python-headless) to read QR codes from a
local image. The decode runs with a timeout guard from ``AppConfig`` so a
pathological image cannot hang the app. The image is validated and pixel-limited
before decoding. No payload is logged, no URL is opened, and nothing is executed.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from office_toolkit.core.config import get_config
from office_toolkit.core.errors import DecodeError, ResourceLimitError, ValidationError
from office_toolkit.core.file_validation import validate_input_file

from .common import check_input_size


@dataclass
class DecodedQr:
    """One decoded QR payload and its position (module-space bounding polygon)."""

    text: str
    points: Optional[list] = None


@dataclass
class DecodeResult:
    """Result of decoding a single image (may contain several QR codes)."""

    found: bool
    items: List[DecodedQr] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _open_cv_image(path: Path):
    import cv2
    import numpy as np

    data = path.read_bytes()
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise DecodeError("Gambar tidak dapat dibaca oleh decoder.")
    return img


def decode_qr(image_path: str | Path, max_items: int = 10) -> DecodeResult:
    """Decode all QR codes found in ``image_path``.

    Raises ``DecodeError`` for unreadable/non-image files and
    ``ResourceLimitError`` when decode takes longer than the configured timeout
    or when the image exceeds the pixel cap.
    """
    p = Path(image_path)
    v = validate_input_file(p)
    if not v.valid:
        raise ValidationError(v.errors[0] if v.errors else f"File tidak valid: {p}")
    check_input_size(p)

    # Pre-validate with Pillow so a non-image file fails with a clear error and
    # the documented pixel limit is enforced before feeding a decoder.
    try:
        from PIL import Image

        with Image.open(p) as im:
            im.load()
            if im.width * im.height > get_config().max_image_pixels:
                raise ResourceLimitError(
                    f"Gambar melebihi batas {get_config().max_image_pixels} piksel."
                )
    except ResourceLimitError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        raise DecodeError(f"Bukan gambar yang dapat dibaca: {e}")

    import cv2

    img = _open_cv_image(p)
    detector = cv2.QRCodeDetector()
    timeout = get_config().qr_decode_timeout_sec

    def run() -> tuple:
        return detector.detectAndDecodeMulti(img)

    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(run)
            ok, decoded, points, _straight = future.result(timeout=timeout)
    except FutureTimeout:
        raise ResourceLimitError(
            f"Decode QR melebihi waktu batas {timeout} detik dan dihentikan."
        )

    if not ok:
        return DecodeResult(found=False, items=[], warnings=[])
    items: List[DecodedQr] = []
    warnings: List[str] = []
    for i, text in enumerate(decoded):
        if not text:
            warnings.append(f"QR ke-{i + 1} terdeteksi tetapi tidak dapat dibaca.")
            continue
        pts = None
        try:
            pts = points[i].tolist() if points is not None and i < len(points) else None
        except Exception:
            pts = None
        items.append(DecodedQr(text=text, points=pts))
        if len(items) >= max_items:
            break
    return DecodeResult(found=bool(items), items=items, warnings=warnings)