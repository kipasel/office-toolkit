"""Unit tests for PDF annotations and image signatures (Phase 4, Fitur F-G)."""

import pymupdf
from PIL import Image

import pytest

from office_toolkit.core.errors import ValidationError
from office_toolkit.services.pdf import edit
from fixtures.pdf_factory import make_pdf


def _annot_count(path, page_index):
    with pymupdf.open(str(path)) as doc:
        annots = doc[page_index].annots()
        return 0 if annots is None else len(list(annots))


def _make_text_pdf(tmp_path, text="TARGET UNIQUE KATA"):
    return make_pdf(tmp_path / "t.pdf", [f"{text} halo", "halaman kedua"])


def test_highlight_found_creates_annotation(pdf_factory, tmp_path):
    src = _make_text_pdf(tmp_path)
    res = edit.annotate_pdf(src, "1", tmp_path / "out", annot_type="highlight", highlight_text="TARGET")
    assert res.annots_added == 1
    assert res.not_found == []
    assert _annot_count(res.output, 0) == 1


def test_highlight_missing_no_fake(pdf_factory, tmp_path):
    src = _make_text_pdf(tmp_path)
    res = edit.annotate_pdf(src, "1", tmp_path / "out", annot_type="highlight", highlight_text="TIDAK ADA")
    assert res.annots_added == 0
    assert len(res.not_found) == 1
    assert "tidak dibuat highlight palsu" in res.not_found[0]
    assert _annot_count(res.output, 0) == 0


def test_note_content_not_on_page(pdf_factory, tmp_path):
    src = _make_text_pdf(tmp_path)
    res = edit.annotate_pdf(
        src, "1", tmp_path / "out",
        annot_type="note", note_pos=(180, 100), note_text="isi-catatan-rahasia",
    )
    assert res.annots_added == 1
    assert _annot_count(res.output, 0) == 1
    with pymupdf.open(str(res.output)) as doc:
        page_text = doc[0].get_text()
    assert "isi-catatan-rahasia" not in page_text


def test_rect_annotation(pdf_factory, tmp_path):
    src = _make_text_pdf(tmp_path)
    res = edit.annotate_pdf(
        src, "1", tmp_path / "out",
        annot_type="rect", rect=(20, 20, 120, 60),
    )
    assert res.annots_added == 1
    assert _annot_count(res.output, 0) == 1


def test_line_arrow_annotation(pdf_factory, tmp_path):
    src = _make_text_pdf(tmp_path)
    res = edit.annotate_pdf(
        src, "1", tmp_path / "out",
        annot_type="line", line_p1=(10, 10), line_p2=(90, 90), arrow=True,
    )
    assert res.annots_added == 1
    assert _annot_count(res.output, 0) == 1


def test_invalid_annotation_type(pdf_factory, tmp_path):
    src = _make_text_pdf(tmp_path)
    with pytest.raises(ValidationError):
        edit.annotate_pdf(src, "1", tmp_path / "out", annot_type="underline")


def test_annotation_source_untouched(pdf_factory, tmp_path):
    src = _make_text_pdf(tmp_path)
    before = src.read_bytes()
    edit.annotate_pdf(src, "1", tmp_path / "out", annot_type="rect", rect=(1, 1, 10, 10))
    assert src.read_bytes() == before


def test_signature_image_places_on_page(sample_pdf, tmp_path):
    img = tmp_path / "sig.png"
    Image.new("RGBA", (120, 60), (0, 0, 0, 200)).save(img)
    res = edit.add_signature_image(sample_pdf, img, 2, tmp_path / "out", x=30, y=40, width_pt=80)
    assert res.placed_page == 2
    assert res.output.exists()
    assert any("BUKAN tanda tangan digital" in w for w in res.warnings)
    with pymupdf.open(str(res.output)) as doc:
        assert doc.page_count == 5
        assert len(doc[1].get_images()) >= 1


def test_signature_invalid_page_rejected(sample_pdf, tmp_path):
    img = tmp_path / "sig.png"
    Image.new("RGB", (10, 10), "red").save(img)
    with pytest.raises(ValidationError):
        edit.add_signature_image(sample_pdf, img, 99, tmp_path / "out")