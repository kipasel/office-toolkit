"""Unit tests for adding text and images to PDFs (Phase 4, Fitur D-E)."""

import pymupdf
from PIL import Image

import pytest

from office_toolkit.core.errors import ValidationError
from office_toolkit.services.pdf import edit
from fixtures.pdf_factory import read_page_texts


def test_add_text_appears_on_target_page(sample_pdf, tmp_path):
    res = edit.add_text_to_pdf(
        sample_pdf, "Teks baru B-42", "3", tmp_path / "out",
        x=40, y=50, box_width=300, fontsize=14, align="center",
    )
    assert res.page_count == 5
    assert res.inserted_pages == [3]
    texts = read_page_texts(res.output)
    assert "B-42" in texts[2]  # page 3
    assert "B-42" not in " ".join(texts[:2])


def test_add_text_to_multiple_pages(sample_pdf, tmp_path):
    res = edit.add_text_to_pdf(sample_pdf, "PAGU-99", "1,3,5", tmp_path / "out", y=90)
    assert res.inserted_pages == [1, 3, 5]


def test_add_text_invalid_coordinate_rejected(sample_pdf, tmp_path):
    with pytest.raises(ValidationError):
        edit.add_text_to_pdf(sample_pdf, "teks", "1", tmp_path / "out", x=10000, y=10000)


def test_add_text_empty_rejected(sample_pdf, tmp_path):
    with pytest.raises(ValidationError):
        edit.add_text_to_pdf(sample_pdf, "   ", "1", tmp_path / "out")


def test_add_unicode_text_completes(sample_pdf, tmp_path):
    res = edit.add_text_to_pdf(sample_pdf, "Harga sedunia \u20ac 100%", "1", tmp_path / "out")
    assert res.output.exists()
    assert res.page_count == 5


def test_add_text_source_untouched(sample_pdf, tmp_path):
    before = sample_pdf.read_bytes()
    edit.add_text_to_pdf(sample_pdf, "X", "1", tmp_path / "out")
    assert sample_pdf.read_bytes() == before


def test_add_image_preserves_aspect_ratio(sample_pdf, tmp_path):
    img = tmp_path / "logo.png"
    Image.new("RGBA", (200, 100), "blue").save(img)
    res = edit.add_image_to_pdf(sample_pdf, img, "1", tmp_path / "out", x=10, y=10, width_pt=100)
    x, y, w, h = res.rect
    assert round(w / h, 2) == round(200 / 100, 2)  # aspect 2:1
    with pymupdf.open(str(res.output)) as doc:
        assert len(doc[0].get_images()) >= 1


def test_add_image_to_range_of_pages(sample_pdf, tmp_path):
    img = tmp_path / "logo.png"
    Image.new("RGBA", (80, 40), "green").save(img)
    res = edit.add_image_to_pdf(sample_pdf, img, "2-4", tmp_path / "out", x=20, y=20, width_pt=60)
    assert res.placed_pages == [2, 3, 4]
    with pymupdf.open(str(res.output)) as doc:
        assert doc.page_count == 5
        assert len(doc[1].get_images()) >= 1
        assert len(doc[2].get_images()) >= 1
        assert len(doc[3].get_images()) >= 1
        assert len(doc[4].get_images()) == 0


def test_add_image_out_of_page_scaled_down(sample_pdf, tmp_path):
    img = tmp_path / "logo.png"
    Image.new("RGB", (100, 100), "red").save(img)
    res = edit.add_image_to_pdf(sample_pdf, img, "1", tmp_path / "out", x=150, y=100, width_pt=1000)
    x, y, w, h = res.rect
    assert x + w <= 200.0 and y + h <= 120.0
    assert any("halaman" in wmsg.lower() for wmsg in res.warnings)


def test_add_image_invalid_page_rejected(sample_pdf, tmp_path):
    img = tmp_path / "logo.png"
    Image.new("RGB", (10, 10), "red").save(img)
    with pytest.raises(ValidationError):
        edit.add_image_to_pdf(sample_pdf, img, "99", tmp_path / "out")


def test_add_image_source_untouched(sample_pdf, tmp_path):
    img = tmp_path / "logo.png"
    Image.new("RGB", (10, 10), "red").save(img)
    before_img = img.read_bytes()
    before_pdf = sample_pdf.read_bytes()
    edit.add_image_to_pdf(sample_pdf, img, "1", tmp_path / "out")
    assert img.read_bytes() == before_img
    assert sample_pdf.read_bytes() == before_pdf