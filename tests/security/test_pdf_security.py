"""Security-focused tests for PDF operations (no real documents)."""

import hashlib

import pytest

from office_toolkit.core.config import AppConfig
from office_toolkit.core.errors import OutputError, PasswordError, ResourceLimitError
from office_toolkit.services.pdf import processor


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_sources_never_modified(sample_pdf, tmp_path):
    before = _sha256(sample_pdf)
    processor.extract_pages(sample_pdf, [1, 2], tmp_path / "e")
    processor.reorder_pages(sample_pdf, [5, 4, 3, 2, 1], tmp_path / "r")
    processor.rotate_pages(sample_pdf, [1], 90, tmp_path / "t")
    processor.split_each_page(sample_pdf, tmp_path / "s")
    processor.split_by_ranges(sample_pdf, [(1, 2)], tmp_path / "sr")
    assert _sha256(sample_pdf) == before


@pytest.mark.parametrize(
    "op",
    [
        lambda p, out: processor.extract_pages(p, [1], out),
        lambda p, out: processor.reorder_pages(p, [1, 2], out),
        lambda p, out: processor.rotate_pages(p, [1], 90, out),
        lambda p, out: processor.split_each_page(p, out),
        lambda p, out: processor.split_by_ranges(p, [(1, 1)], out),
    ],
)
def test_encrypted_pdf_rejected_without_cracking(encrypted_pdf, tmp_path, op):
    with pytest.raises(PasswordError) as exc:
        op(encrypted_pdf, tmp_path / "out")
    assert "rahasia" not in str(exc.value)


def test_merge_encrypted_does_not_leak_password(tmp_path, pdf_factory):
    a = pdf_factory.make_pdf(tmp_path / "a.pdf", ["A1"])
    enc = pdf_factory.make_encrypted_pdf(tmp_path / "e.pdf", user_pw="super-secret")
    with pytest.raises(PasswordError) as exc:
        processor.merge_pdfs([a, enc], tmp_path / "out")
    assert "super-secret" not in str(exc.value)


def test_no_temp_leftover_after_failure(corrupt_pdf, tmp_path):
    out_dir = tmp_path / "out"
    with pytest.raises(Exception):
        processor.extract_pages(corrupt_pdf, [1], out_dir)
    leftovers = list(out_dir.glob("otk_*")) if out_dir.exists() else []
    assert leftovers == []


def test_illegal_output_name_is_sanitized(sample_pdf, tmp_path):
    res = processor.extract_pages(sample_pdf, [1], tmp_path / "out", output_name="bad:na*me?.pdf")
    assert ":" not in res.output.name
    assert "*" not in res.output.name
    assert "?" not in res.output.name


def test_input_size_limit_enforced(sample_pdf, monkeypatch):
    monkeypatch.setattr(processor, "get_config", lambda: AppConfig(max_input_mb=0))
    with pytest.raises(ResourceLimitError):
        processor.get_pdf_info(sample_pdf)


def test_split_failure_removes_already_created_outputs(sample_pdf, tmp_path, monkeypatch):
    original = processor._save_verified
    calls = {"n": 0}

    def flaky(doc, out_path, expected):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OutputError("simulasi kegagalan penyimpanan")
        return original(doc, out_path, expected)

    monkeypatch.setattr(processor, "_save_verified", flaky)
    out_dir = tmp_path / "out"
    with pytest.raises(OutputError):
        processor.split_by_ranges(sample_pdf, [(1, 1), (2, 2)], out_dir)
    assert list(out_dir.glob("*.pdf")) == []
    assert list(out_dir.glob("otk_*")) == []
