"""Unit tests for QR PNG/SVG export (C4)."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PIL import Image

from office_toolkit.core.errors import ValidationError
from office_toolkit.services.qr.generator import QrDesign, render_qr_png, render_qr_svg


def test_png_export_reopenable(tmp_path):
    res = render_qr_png("https://contoh.id/1", tmp_path / "out")
    assert res.fmt == "PNG"
    assert res.output.exists()
    assert res.output.suffix == ".png"
    with Image.open(res.output) as im:
        im.load()
        assert im.size[0] > 0 and im.size[1] > 0


def test_png_export_size_matches_design(tmp_path):
    res = render_qr_png("data", tmp_path / "out", design=QrDesign(box_size=10, border=4))
    with Image.open(res.output) as im:
        assert im.size[0] >= 10 * 21


def test_png_honours_colors(tmp_path):
    res = render_qr_png("data", tmp_path / "out", design=QrDesign(fg_color="#C00000", bg_color="#FFFFFF"))
    img = Image.open(res.output).convert("RGB")
    colors = img.getcolors(maxcolors=2_000_000)
    assert colors is not None
    palette = {c for _, c in colors}
    assert (192, 0, 0) in palette


def test_png_output_name_respected(tmp_path):
    res = render_qr_png("data", tmp_path / "out", output_name="kodeA")
    assert res.output.name == "kodeA.png"


def test_png_duplicate_name_gets_alternative(tmp_path):
    d = tmp_path / "out"
    first = render_qr_png("data", d, output_name="sama")
    second = render_qr_png("data", d, output_name="sama")
    assert first.output.exists() and second.output.exists()
    assert first.output != second.output
    assert second.output.name == "sama_1.png"


def test_png_empty_data_rejected(tmp_path):
    with pytest.raises(ValidationError):
        render_qr_png("   ", tmp_path / "out")


def test_png_zero_quiet_zone_accepted(tmp_path):
    res = render_qr_png("data", tmp_path / "out", design=QrDesign(border=0))
    assert res.output.exists()


def test_svg_export_structure(tmp_path):
    res = render_qr_svg("https://contoh.id/svg", tmp_path / "out")
    assert res.output.suffix == ".svg"
    root = ET.parse(str(res.output)).getroot()
    assert root.tag.lower().endswith("svg")
    assert any(str(n.tag).lower().endswith("path") for n in root.iter())


def test_svg_honours_fill_color(tmp_path):
    res = render_qr_svg("data", tmp_path / "out", design=QrDesign(fg_color="#006600"))
    content = res.output.read_text(encoding="utf-8")
    assert "#006600" in content.lower()


def test_svg_rejects_logo(tmp_path):
    from fixtures.qr_factory import make_logo

    logo = make_logo(tmp_path / "logo.png")
    with pytest.raises(ValidationError, match="SVG"):
        render_qr_svg("data", tmp_path / "out", design=QrDesign(logo_path=logo))


def test_svg_empty_data_rejected(tmp_path):
    with pytest.raises(ValidationError):
        render_qr_svg("", tmp_path / "out")


def test_no_temp_files_left_behind(tmp_path):
    d = tmp_path / "out"
    render_qr_png("data", d)
    render_qr_svg("data", d)
    leftovers = [p for p in Path(d).iterdir() if p.name.startswith("otk_")]
    assert leftovers == []


def test_svg_and_png_source_not_affected(tmp_path):
    # render functions never read a source document; creating twice to same name
    # must not corrupt either file.
    d = tmp_path / "out"
    a = render_qr_png("AAA", d, output_name="x")
    b = render_qr_png("BBB", d, output_name="x")
    assert a.output.read_bytes() != b.output.read_bytes()
    assert a.output.exists() and b.output.exists()