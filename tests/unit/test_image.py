from pathlib import Path

from PIL import Image, PngImagePlugin

from office_toolkit.services.images import processor


def test_convert_png_to_jpg(tmp_path):
    f = tmp_path / "t.png"
    Image.new("RGBA", (20, 10), (0, 0, 255, 128)).save(f)
    res = processor.convert_image(f, tmp_path, "jpg", quality=85)
    assert res.output.exists()
    assert res.output.suffix.lower() in (".jpg", ".jpeg")
    with Image.open(res.output) as im:
        assert im.mode == "RGB"


def test_resize_keep_aspect(tmp_path):
    f = tmp_path / "t.png"
    Image.new("RGB", (100, 50), "red").save(f)
    res = processor.resize_image(f, tmp_path, width_px=50, keep_aspect=True)
    assert res.new_w == 50
    assert res.new_h == 25


def test_resize_pct(tmp_path):
    f = tmp_path / "t.png"
    Image.new("RGB", (100, 100), "blue").save(f)
    res = processor.resize_image(f, tmp_path, scale_pct=50.0)
    assert res.new_w == 50
    assert res.new_h == 50


def test_get_info(tmp_path):
    f = tmp_path / "t.png"
    Image.new("RGB", (5, 6), "green").save(f)
    info = processor.get_info(f)
    assert info.width == 5
    assert info.height == 6


def test_convert_removes_metadata(tmp_path):
    f = tmp_path / "meta.png"
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", "rahasia")
    Image.new("RGB", (12, 12), "red").save(f, pnginfo=meta)
    with Image.open(f) as im:
        assert im.info.get("Comment") == "rahasia"
    res = processor.convert_image(f, tmp_path, "png", remove_metadata=True)
    with Image.open(res.output) as out:
        assert "Comment" not in out.info


def test_get_info_rejects_missing_file(tmp_path):
    from office_toolkit.core.errors import ValidationError

    try:
        processor.get_info(tmp_path / "tidak-ada.png")
    except ValidationError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected ValidationError for missing file")
