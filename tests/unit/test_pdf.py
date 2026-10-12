"""Unit tests for the PDF Toolkit core processor (synthetic PDFs only)."""

import hashlib
from pathlib import Path

import pytest

from office_toolkit.core.errors import (
    DecodeError,
    PasswordError,
    ValidationError,
)
from office_toolkit.services.pdf import processor
from fixtures.pdf_factory import page_count, read_page_texts


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- info ---------------------------------------------------------------
def test_info_page_count_and_size(sample_pdf):
    info = processor.get_pdf_info(sample_pdf)
    assert info.page_count == 5
    assert info.size_bytes == sample_pdf.stat().st_size
    assert info.encrypted is False
    assert info.needs_password is False
    assert info.page_size is not None


def test_info_empty_metadata_is_none_not_error(pdf_factory, tmp_path):
    p = pdf_factory.make_pdf(tmp_path / "m.pdf", ["A"])
    info = processor.get_pdf_info(p)
    assert info.title is None
    assert info.author is None
    assert info.metadata_error is None


def test_info_corrupt_pdf_raises_decode(corrupt_pdf):
    with pytest.raises(DecodeError):
        processor.get_pdf_info(corrupt_pdf)


def test_info_encrypted_reports_status(encrypted_pdf):
    info = processor.get_pdf_info(encrypted_pdf)
    assert info.encrypted is True
    assert info.needs_password is True
    assert info.page_count is None
    assert info.metadata_error


def test_info_missing_file_raises_validation():
    with pytest.raises(ValidationError):
        processor.get_pdf_info("no_such_file_xyz.pdf")


# --- range/list parsing -------------------------------------------------
def test_parse_page_ranges_valid():
    assert processor.parse_page_ranges("1-3, 5, 7-9", 10) == [(1, 3), (5, 5), (7, 9)]


@pytest.mark.parametrize("spec", ["", "0-2", "3-1", "1-99", "abc", "1-"])
def test_parse_page_ranges_invalid(spec):
    with pytest.raises(ValidationError):
        processor.parse_page_ranges(spec, 5)


def test_parse_pages_expands_ranges_preserving_order():
    assert processor.parse_pages("3, 1, 5-7", 10) == [3, 1, 5, 6, 7]
    assert processor.parse_pages("2, 2, 1", 5) == [2, 2, 1]


@pytest.mark.parametrize("spec", ["", "0", "6", "x", "1,,2-"])
def test_parse_pages_invalid(spec):
    with pytest.raises(ValidationError):
        processor.parse_pages(spec, 5)


# --- merge --------------------------------------------------------------
def test_merge_order_and_count(tmp_path, pdf_factory):
    a = pdf_factory.make_pdf(tmp_path / "a.pdf", ["A1", "A2"])
    b = pdf_factory.make_pdf(tmp_path / "b.pdf", ["B1", "B2", "B3"])
    out_dir = tmp_path / "out"
    res = processor.merge_pdfs([a, b], out_dir)
    assert res.page_count == 5
    assert res.total_input_pages == 5
    assert read_page_texts(res.output) == ["A1", "A2", "B1", "B2", "B3"]


def test_merge_single_input_rejected(tmp_path, pdf_factory):
    a = pdf_factory.make_pdf(tmp_path / "a.pdf", ["A1"])
    with pytest.raises(ValidationError):
        processor.merge_pdfs([a], tmp_path / "out")


def test_merge_missing_input_rejected(tmp_path, pdf_factory):
    a = pdf_factory.make_pdf(tmp_path / "a.pdf", ["A1"])
    with pytest.raises(ValidationError):
        processor.merge_pdfs([a, tmp_path / "missing.pdf"], tmp_path / "out")


def test_merge_encrypted_input_rejected(tmp_path, pdf_factory):
    a = pdf_factory.make_pdf(tmp_path / "a.pdf", ["A1"])
    enc = pdf_factory.make_encrypted_pdf(tmp_path / "e.pdf")
    with pytest.raises(PasswordError):
        processor.merge_pdfs([a, enc], tmp_path / "out")


def test_merge_source_untouched(tmp_path, pdf_factory):
    a = pdf_factory.make_pdf(tmp_path / "a.pdf", ["A1", "A2"])
    b = pdf_factory.make_pdf(tmp_path / "b.pdf", ["B1"])
    before = {a: _sha256(a), b: _sha256(b)}
    processor.merge_pdfs([a, b], tmp_path / "out")
    assert _sha256(a) == before[a]
    assert _sha256(b) == before[b]


def test_merge_name_conflict_uses_alternative(tmp_path, pdf_factory):
    a = pdf_factory.make_pdf(tmp_path / "a.pdf", ["A1"])
    b = pdf_factory.make_pdf(tmp_path / "b.pdf", ["B1"])
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    existing = out_dir / "gabungan.pdf"
    existing.write_bytes(b"keep me")
    res = processor.merge_pdfs([a, b], out_dir)
    assert res.output.name != "gabungan.pdf"
    assert existing.read_bytes() == b"keep me"


# --- split --------------------------------------------------------------
def test_split_by_ranges(sample_pdf, tmp_path):
    out_dir = tmp_path / "out"
    res = processor.split_by_ranges(sample_pdf, [(1, 2), (3, 5)], out_dir)
    assert len(res.outputs) == 2
    texts0 = read_page_texts(res.outputs[0].output)
    texts1 = read_page_texts(res.outputs[1].output)
    assert texts0 == ["P1", "P2"]
    assert texts1 == ["P3", "P4", "P5"]
    assert page_count(res.outputs[0].output) == 2


def test_split_each_page(sample_pdf, tmp_path):
    out_dir = tmp_path / "out"
    res = processor.split_each_page(sample_pdf, out_dir)
    assert len(res.outputs) == 5
    for i, sf in enumerate(res.outputs, start=1):
        assert page_count(sf.output) == 1
        assert read_page_texts(sf.output) == [f"P{i}"]
    names = [sf.output.name for sf in res.outputs]
    assert len(set(names)) == len(names)


def test_split_invalid_range_rejected(sample_pdf, tmp_path):
    with pytest.raises(ValidationError):
        processor.split_by_ranges(sample_pdf, [(1, 99)], tmp_path / "out")


# --- extract ------------------------------------------------------------
def test_extract_single_and_order(sample_pdf, tmp_path):
    res = processor.extract_pages(sample_pdf, [3, 1, 5], tmp_path / "out")
    assert res.page_count == 3
    assert read_page_texts(res.output) == ["P3", "P1", "P5"]


def test_extract_duplicates_preserved(sample_pdf, tmp_path):
    res = processor.extract_pages(sample_pdf, [2, 2, 1], tmp_path / "out")
    assert read_page_texts(res.output) == ["P2", "P2", "P1"]


def test_extract_out_of_range_rejected(sample_pdf, tmp_path):
    with pytest.raises(ValidationError):
        processor.extract_pages(sample_pdf, [1, 99], tmp_path / "out")


def test_extract_source_untouched(sample_pdf, tmp_path):
    before = _sha256(sample_pdf)
    processor.extract_pages(sample_pdf, [1, 2], tmp_path / "out")
    assert _sha256(sample_pdf) == before


# --- reorder ------------------------------------------------------------
def test_reorder_changes_order(tmp_path, pdf_factory):
    p = pdf_factory.make_pdf(tmp_path / "r.pdf", ["R1", "R2", "R3"])
    res = processor.reorder_pages(p, [3, 1, 2], tmp_path / "out")
    assert res.page_count == 3
    assert read_page_texts(res.output) == ["R3", "R1", "R2"]


def test_reorder_requires_full_permutation(tmp_path, pdf_factory):
    p = pdf_factory.make_pdf(tmp_path / "r.pdf", ["R1", "R2", "R3"])
    with pytest.raises(ValidationError):
        processor.reorder_pages(p, [1, 2], tmp_path / "out")


def test_reorder_duplicate_rejected(tmp_path, pdf_factory):
    p = pdf_factory.make_pdf(tmp_path / "r.pdf", ["R1", "R2", "R3"])
    with pytest.raises(ValidationError):
        processor.reorder_pages(p, [1, 1, 2], tmp_path / "out")


# --- rotate -------------------------------------------------------------
@pytest.mark.parametrize("angle", [90, 180, 270])
def test_rotate_selected_page(sample_pdf, tmp_path, angle):
    res = processor.rotate_pages(sample_pdf, [1], angle, tmp_path / "out")
    with processor.pymupdf.open(str(res.output)) as doc:
        assert doc[0].rotation == angle
        assert doc[1].rotation == 0
    assert res.angle == angle
    assert res.page_count == 5


def test_rotate_all_pages(sample_pdf, tmp_path):
    res = processor.rotate_pages(sample_pdf, list(range(1, 6)), 180, tmp_path / "out")
    with processor.pymupdf.open(str(res.output)) as doc:
        assert all(doc[i].rotation == 180 for i in range(doc.page_count))


def test_rotate_invalid_angle(sample_pdf, tmp_path):
    with pytest.raises(ValidationError):
        processor.rotate_pages(sample_pdf, [1], 45, tmp_path / "out")


def test_rotate_invalid_page(sample_pdf, tmp_path):
    with pytest.raises(ValidationError):
        processor.rotate_pages(sample_pdf, [99], 90, tmp_path / "out")


# --- output safety ------------------------------------------------------
def test_output_dir_is_file_rejected(sample_pdf, tmp_path):
    not_a_dir = tmp_path / "afile.txt"
    not_a_dir.write_text("x")
    with pytest.raises(ValidationError):
        processor.extract_pages(sample_pdf, [1], not_a_dir)


def test_temp_files_cleaned(sample_pdf, tmp_path):
    out_dir = tmp_path / "out"
    processor.extract_pages(sample_pdf, [1, 2], out_dir)
    leftovers = list(out_dir.glob("otk_*"))
    assert leftovers == []


def test_corrupt_input_rejected_for_operations(corrupt_pdf, tmp_path):
    with pytest.raises(DecodeError):
        processor.extract_pages(corrupt_pdf, [1], tmp_path / "out")
