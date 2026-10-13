"""Unit tests for image -> PDF (Phase 4, Fitur C) - synthetic images only."""

import pymupdf
from PIL import Image

import pytest

from office_toolkit.core.errors import ProcessingError, ValidationError
from office_toolkit.services.pdf import from_images
from fixtures.pdf_factory import page_count


def _page_dims(path, n=0):
    with pymupdf.open(str(path)) as doc:
        r = doc[n].rect
        return round(r.width, 1), round(r.height, 1)


def test_single_image_auto_size(tmp_path):
    img = tmp_path / "a.png"
    Image.new("RGB", (300, 200), "red").save(img)
    res = from_images.images_to_pdf([img], tmp_path / "out")
    assert res.page_count == 1
    assert res.failed == []
    assert page_count(res.output) == 1
    assert _page_dims(res.output) == (300.0, 200.0)


def test_multiple_images_preserve_order(tmp_path):
    paths = []
    for i, size in enumerate([(100, 100), (200, 150), (50, 300)]):
        p = tmp_path / f"{i}.png"
        Image.new("RGB", size, "blue").save(p)
        paths.append(p)
    res = from_images.images_to_pdf(paths, tmp_path / "out")
    assert res.page_count == 3
    with pymupdf.open(str(res.output)) as doc:
        dims = [(round(doc[i].rect.width, 1), round(doc[i].rect.height, 1)) for i in range(3)]
    assert dims == [(100.0, 100.0), (200.0, 150.0), (50.0, 300.0)]


def test_transparency_flattened_on_white(tmp_path):
    img = tmp_path / "t.png"
    Image.new("RGBA", (60, 40), (0, 128, 255, 100)).save(img)
    res = from_images.images_to_pdf([img], tmp_path / "out", background="white")
    assert page_count(res.output) == 1


def test_exif_orientation_applied(tmp_path):
    img = tmp_path / "e.jpg"
    im = Image.new("RGB", (200, 100), "green")
    exif = Image.Exif()
    exif[0x0112] = 6
    im.save(img, format="JPEG", exif=exif)
    res = from_images.images_to_pdf([img], tmp_path / "out")
    assert _page_dims(res.output) == (100.0, 200.0)


def test_tiff_multi_frame_only_first(tmp_path):
    img = tmp_path / "m.tif"
    first = Image.new("RGB", (70, 40), "red")
    second = Image.new("RGB", (90, 120), "blue")
    first.save(img, save_all=True, append_images=[second], format="TIFF")
    res = from_images.images_to_pdf([img], tmp_path / "out")
    assert res.page_count == 1
    assert any("multi-halaman" in w for w in res.warnings)
    assert _page_dims(res.output) == (70.0, 40.0)


def test_corrupt_image_reported_not_fatal(tmp_path):
    good = tmp_path / "good.png"
    Image.new("RGB", (20, 20), "red").save(good)
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not really a png")
    res = from_images.images_to_pdf([good, bad], tmp_path / "out")
    assert res.page_count == 1
    assert len(res.failed) == 1
    assert res.failed[0][0] == "bad.png"


def test_all_images_corrupt_raises(tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"garbage")
    with pytest.raises(ProcessingError):
        from_images.images_to_pdf([bad], tmp_path / "out")


def test_invalid_page_size_rejected(tmp_path):
    img = tmp_path / "a.png"
    Image.new("RGB", (10, 10), "red").save(img)
    with pytest.raises(ValidationError):
        from_images.images_to_pdf([img], tmp_path / "out", page_size="tabloid")


def test_fixed_a4_landscape_orientation(tmp_path):
    img = tmp_path / "a.png"
    Image.new("RGB", (100, 200), "red").save(img)
    res = from_images.images_to_pdf(
        [img], tmp_path / "out", page_size="a4", orientation="landscape", fit_mode="fit"
    )
    w, h = _page_dims(res.output)
    assert w > h  # landscape A4


def test_images_to_pdf_source_untouched(tmp_path):
    img = tmp_path / "a.png"
    before = Image.new("RGB", (40, 30), "blue")
    before.save(img)
    raw = img.read_bytes()
    from_images.images_to_pdf([img], tmp_path / "out")
    assert img.read_bytes() == raw


def test_no_temp_leftover(tmp_path):
    img = tmp_path / "a.png"
    Image.new("RGB", (20, 20), "red").save(img)
    from_images.images_to_pdf([img], tmp_path / "out")
    leftovers = list((tmp_path / "out").glob("otk_*"))
    assert leftovers == []