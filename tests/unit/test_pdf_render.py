"""Unit tests for rendering PDF pages to PNG/JPEG (Phase 4, Fitur B)."""

from PIL import Image

import pytest

from office_toolkit.core.errors import PasswordError, ValidationError
from office_toolkit.services.pdf import render


def test_render_all_pages_png(sample_pdf, tmp_path):
    res = render.render_pdf_to_images(sample_pdf, tmp_path / "out", fmt="png", dpi=100)
    assert res.rendered_count == 5
    assert res.page_count == 5
    assert res.failed == []
    names = [f.output.name for f in res.outputs]
    assert names == [f"sample_page_00{i}.png" for i in range(1, 6)]
    for f in res.outputs:
        with Image.open(f.output) as im:
            im.load()
            assert im.mode == "RGB"


def test_render_range_and_jpeg(sample_pdf, tmp_path):
    res = render.render_pdf_to_images(sample_pdf, tmp_path / "out", pages="2-4", fmt="jpg", dpi=100)
    assert res.rendered_count == 3
    assert [f.output.name for f in res.outputs] == [
        "sample_page_002.jpg",
        "sample_page_003.jpg",
        "sample_page_004.jpg",
    ]


def test_render_invalid_format_rejected(sample_pdf, tmp_path):
    with pytest.raises(ValidationError):
        render.render_pdf_to_images(sample_pdf, tmp_path / "out", fmt="gif")


@pytest.mark.parametrize("dpi", [10, 1000])
def test_render_dpi_out_of_range_rejected(sample_pdf, tmp_path, dpi):
    with pytest.raises(ValidationError):
        render.render_pdf_to_images(sample_pdf, tmp_path / "out", dpi=dpi)


def test_render_name_conflict_uses_alternative(sample_pdf, tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True)
    (out_dir / "sample_page_001.png").write_bytes(b"keep-me")
    res = render.render_pdf_to_images(sample_pdf, out_dir, pages="1", fmt="png", dpi=72)
    assert res.outputs[0].output.name != "sample_page_001.png"
    assert (out_dir / "sample_page_001.png").read_bytes() == b"keep-me"


def test_render_encrypted_rejected(encrypted_pdf, tmp_path):
    with pytest.raises(PasswordError):
        render.render_pdf_to_images(encrypted_pdf, tmp_path / "out")


def test_render_source_untouched(sample_pdf, tmp_path):
    before = sample_pdf.read_bytes()
    render.render_pdf_to_images(sample_pdf, tmp_path / "out")
    assert sample_pdf.read_bytes() == before


def test_render_out_of_range_page_rejected(sample_pdf, tmp_path):
    with pytest.raises(ValidationError):
        render.render_pdf_to_images(sample_pdf, tmp_path / "out", pages="1, 99")


def test_render_no_temp_leftover(sample_pdf, tmp_path):
    render.render_pdf_to_images(sample_pdf, tmp_path / "out", pages="1-2")
    leftovers = list((tmp_path / "out").glob("otk_*"))
    assert leftovers == []