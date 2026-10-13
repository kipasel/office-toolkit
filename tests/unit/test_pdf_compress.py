"""Unit tests for PDF compression (Phase 4, Fitur A) - synthetic PDFs only."""

import hashlib

import pytest

from office_toolkit.core.errors import PasswordError, ValidationError
from office_toolkit.services.pdf import compress
from fixtures.pdf_factory import read_page_texts


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_structure_mode_preserves_text_and_pages(pdf_factory, tmp_path):
    src = pdf_factory.make_pdf_with_image(tmp_path / "s.pdf", ["G1", "G2"])
    res = compress.compress_pdf(src, tmp_path / "out", "struktur")
    assert res.mode == "struktur"
    assert res.page_count == 2
    assert res.output.exists()
    with compress.open_pdf(res.output) as doc:
        assert doc.page_count == 2
    assert read_page_texts(res.output) == ["G1", "G2"]


def test_images_mode_keeps_searchable_text(pdf_factory, tmp_path):
    src = pdf_factory.make_pdf_with_image(tmp_path / "s.pdf", ["TEKS_CARI"])
    res = compress.compress_pdf(src, tmp_path / "out", "images", quality=60)
    assert res.output.exists()
    assert any("lossy" in w for w in res.warnings)
    assert "TEKS_CARI" in read_page_texts(res.output)[0]


def test_rasterize_warns_and_keeps_page_count(pdf_factory, tmp_path):
    src = pdf_factory.make_pdf_with_image(tmp_path / "s.pdf", ["RASTER1"])
    res = compress.compress_pdf(src, tmp_path / "out", "rasterize", rasterize_dpi=100)
    assert res.output.exists()
    assert res.page_count == 1
    assert any("rasterisasi" in w for w in res.warnings)
    assert any("TIDAK dipertahankan" in w for w in res.warnings)
    with compress.open_pdf(res.output) as doc:
        assert doc.page_count == 1


def test_invalid_mode_rejected(pdf_factory, tmp_path):
    src = pdf_factory.make_pdf(tmp_path / "s.pdf", ["A"])
    with pytest.raises(ValidationError):
        compress.compress_pdf(src, tmp_path / "out", "hocus")


@pytest.mark.parametrize("quality", [0, 101])
def test_invalid_quality_rejected(pdf_factory, tmp_path, quality):
    src = pdf_factory.make_pdf(tmp_path / "s.pdf", ["A"])
    with pytest.raises(ValidationError):
        compress.compress_pdf(src, tmp_path / "out", "images", quality=quality)


def test_savings_formula_reported(pdf_factory, tmp_path):
    src = pdf_factory.make_pdf(tmp_path / "s.pdf", ["A"])
    res = compress.compress_pdf(src, tmp_path / "out", "struktur")
    expected = (res.input_size - res.output_size) / res.input_size * 100.0
    assert res.savings_pct == pytest.approx(expected, abs=1e-9)


def test_source_untouched(pdf_factory, tmp_path):
    src = pdf_factory.make_pdf_with_image(tmp_path / "s.pdf", ["G1"])
    before = _sha256(src)
    for mode in ("struktur", "images", "rasterize"):
        compress.compress_pdf(src, tmp_path / f"o_{mode}", mode)
    assert _sha256(src) == before


def test_encrypted_source_rejected(encrypted_pdf, tmp_path):
    with pytest.raises(PasswordError):
        compress.compress_pdf(encrypted_pdf, tmp_path / "out", "struktur")


def test_no_temp_leftover(pdf_factory, tmp_path):
    src = pdf_factory.make_pdf(tmp_path / "s.pdf", ["A"])
    compress.compress_pdf(src, tmp_path / "out", "struktur")
    leftovers = list((tmp_path / "out").glob("otk_*"))
    assert leftovers == []