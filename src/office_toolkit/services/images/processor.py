from __future__ import annotations

import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageOps

from office_toolkit.core.errors import ProcessingError, ValidationError
from office_toolkit.core.file_validation import validate_input_file
from office_toolkit.core.output_manager import OutputManager


@dataclass
class ImageInfo:
    path: Path
    format: str
    width: int
    height: int
    size_bytes: int
    has_transparency: bool


@dataclass
class ConvertResult:
    input: Path
    output: Path
    input_size: int
    output_size: int
    savings_pct: float


@dataclass
class ResizeResult:
    input: Path
    output: Path
    input_size: int
    output_size: int
    old_w: int
    old_h: int
    new_w: int
    new_h: int
    savings_pct: float


SUPPORTED = {"jpg", "jpeg", "png", "webp", "bmp", "tiff", "tif"}


def get_info(path: Path) -> ImageInfo:
    v = validate_input_file(path)
    if not v.valid:
        raise ValidationError(v.errors[0] if v.errors else "File tidak valid")
    try:
        with Image.open(path) as im:
            im.load()
            fmt = im.format or ""
            has_trans = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
            return ImageInfo(
                path=path,
                format=fmt,
                width=im.width,
                height=im.height,
                size_bytes=path.stat().st_size,
                has_transparency=has_trans,
            )
    except Exception as e:
        raise ProcessingError(f"Gagal membaca gambar: {e}")


def _save_image(img: Image.Image, out_path: Path, fmt_out: str, quality: int, remove_metadata: bool) -> None:
    if fmt_out == "JPEG":
        if img.mode in ("RGBA", "LA"):
            bg = Image.new("RGB", img.size, "white")
            bg.paste(img, mask=img.split()[-1] if img.mode != "LA" else img.convert("RGBA").split()[-1])
            img_out = bg
        else:
            img_out = img.convert("RGB")
        save_opts = {"quality": quality, "optimize": True}
        if remove_metadata:
            save_opts["exif"] = b""
        img_out.save(out_path, format="JPEG", **save_opts)
    elif fmt_out == "PNG":
        save_opts = {"optimize": True}
        if remove_metadata:
            save_opts["info"] = {}
        img.save(out_path, format="PNG", **save_opts)
    elif fmt_out == "WEBP":
        save_opts = {"quality": quality, "optimize": True}
        if remove_metadata:
            save_opts["exif"] = b""
        img.save(out_path, format="WEBP", **save_opts)
    elif fmt_out == "BMP":
        img.convert("RGB").save(out_path, format="BMP")
    elif fmt_out == "TIFF":
        save_opts = {"compression": "tiff_lzw"}
        if remove_metadata:
            save_opts["exif"] = b""
        img.convert("RGB").save(out_path, format="TIFF", **save_opts)
    else:
        img.save(out_path, format=fmt_out)


def convert_image(
    input_path: Path,
    output_dir: Path,
    target_format: str,
    quality: int = 90,
    background: str = "white",
    remove_metadata: bool = False,
) -> ConvertResult:
    v = validate_input_file(input_path)
    if not v.valid:
        raise ValidationError(v.errors[0] if v.errors else "File tidak valid")

    fmt = target_format.lower().strip()
    if fmt == "jpg":
        fmt_out = "JPEG"
        ext = ".jpg"
    elif fmt == "jpeg":
        fmt_out = "JPEG"
        ext = ".jpeg"
    elif fmt == "png":
        fmt_out = "PNG"
        ext = ".png"
    elif fmt == "webp":
        fmt_out = "WEBP"
        ext = ".webp"
    elif fmt == "bmp":
        fmt_out = "BMP"
        ext = ".bmp"
    elif fmt == "tiff" or fmt == "tif":
        fmt_out = "TIFF"
        ext = ".tif" if fmt == "tif" else ".tiff"
    else:
        raise ValidationError(f"Format tidak didukung: {target_format}")

    om = OutputManager()
    out_path = om.safe_output_path(input_path.stem + ext, dir_path=output_dir, allow_overwrite=False)

    try:
        with Image.open(input_path) as im:
            im.load()
            img = im
            _save_image(img, out_path, fmt_out, quality, remove_metadata)
    except Exception as e:
        om.cleanup(out_path)
        raise ProcessingError(f"Gagal konversi: {e}")

    out_size = out_path.stat().st_size
    in_size = input_path.stat().st_size
    if in_size == 0:
        savings = 0.0
    else:
        savings = (in_size - out_size) / in_size * 100.0
    return ConvertResult(input=input_path, output=out_path, input_size=in_size, output_size=out_size, savings_pct=savings)


def resize_image(
    input_path: Path,
    output_dir: Path,
    width_px: Optional[int] = None,
    height_px: Optional[int] = None,
    scale_pct: Optional[float] = None,
    keep_aspect: bool = True,
    quality: int = 90,
    target_format: Optional[str] = None,
) -> ResizeResult:
    v = validate_input_file(input_path)
    if not v.valid:
        raise ValidationError(v.errors[0] if v.errors else "File tidak valid")

    with Image.open(input_path) as im:
        im.load()
        w, h = im.width, im.height

    if scale_pct is not None:
        if scale_pct <= 0:
            raise ValidationError("Scale persentase harus > 0")
        nw, nh = int(w * scale_pct / 100.0), int(h * scale_pct / 100.0)
    else:
        if width_px is None and height_px is None:
            raise ValidationError("Tentukan width_px/height_px atau scale_pct")
        if width_px is not None and width_px <= 0:
            raise ValidationError("Lebar harus > 0")
        if height_px is not None and height_px <= 0:
            raise ValidationError("Tinggi harus > 0")
        if keep_aspect and width_px is not None and height_px is not None:
            nw, nh = width_px, height_px
        elif keep_aspect and width_px is not None:
            ratio = h / w if w > 0 else 1
            nw, nh = width_px, int(width_px * ratio)
        elif keep_aspect and height_px is not None:
            ratio = w / h if h > 0 else 1
            nw, nh = int(height_px * ratio), height_px
        else:
            nw = width_px or w
            nh = height_px or h

    if nw < 1 or nh < 1:
        raise ValidationError("Dimensi hasil tidak valid")
    if nw > 100000 or nh > 100000:
        raise ValidationError("Dimensi terlalu besar")

    fmt_out = target_format.lower() if target_format else "png"
    if fmt_out == "jpg":
        fmt_out_code, ext = "JPEG", ".jpg"
    elif fmt_out == "jpeg":
        fmt_out_code, ext = "JPEG", ".jpeg"
    elif fmt_out == "webp":
        fmt_out_code, ext = "WEBP", ".webp"
    else:
        fmt_out_code, ext = "PNG", ".png"

    om = OutputManager()
    out_path = om.safe_output_path(input_path.stem + "_resized" + ext, dir_path=output_dir, allow_overwrite=False)

    try:
        with Image.open(input_path) as im:
            im.load()
            resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
            _save_image(resized, out_path, fmt_out_code, quality, False)
    except Exception as e:
        om.cleanup(out_path)
        raise ProcessingError(f"Gagal resize: {e}")

    out_size = out_path.stat().st_size
    in_size = input_path.stat().st_size
    savings = (in_size - out_size) / in_size * 100.0 if in_size > 0 else 0.0
    return ResizeResult(input=input_path, output=out_path, input_size=in_size, output_size=out_size, old_w=w, old_h=h, new_w=nw, new_h=nh, savings_pct=savings)
