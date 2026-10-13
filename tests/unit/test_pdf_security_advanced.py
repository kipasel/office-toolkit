"""Unit tests for PDF password protection and authorized decryption (Fitur H-I)."""

import pymupdf

import pytest

from office_toolkit.core.errors import PasswordError, ValidationError
from office_toolkit.services.pdf import security
from fixtures.pdf_factory import read_page_texts


def _state(path):
    with pymupdf.open(str(path)) as doc:
        return {
            "needs_pass": bool(doc.needs_pass),
            "encrypted": bool(doc.is_encrypted),
            "pages": doc.page_count,
        }


def test_encrypt_creates_real_password_protection(sample_pdf, tmp_path):
    res = security.encrypt_pdf(sample_pdf, "user1234", "owner1234", tmp_path / "out")
    assert res.algorithm == "AES-256"
    assert res.is_encrypted is True
    state = _state(res.output)
    assert state["needs_pass"] is True
    assert state["encrypted"] is True
    assert state["pages"] == 5

    with pymupdf.open(str(res.output)) as doc:
        assert doc.authenticate("user1234") != 0
        assert doc.page_count == 5
    with pymupdf.open(str(res.output)) as doc:
        assert doc.authenticate("salah-pass") == 0


def test_encrypt_disabled_permissions_are_not_granted(sample_pdf, tmp_path):
    res = security.encrypt_pdf(
        sample_pdf, "user1234", "owner1234", tmp_path / "out",
        algorithm="AES-128",
        allow_print=False, allow_copy=False, allow_modify=False, allow_annotate=False,
    )
    assert res.algorithm == "AES-128"
    with pymupdf.open(str(res.output)) as doc:
        doc.authenticate("user1234")
        perms = doc.permissions
        assert perms & pymupdf.PDF_PERM_PRINT == 0


def test_encrypt_empty_password_rejected(sample_pdf, tmp_path):
    with pytest.raises(ValidationError):
        security.encrypt_pdf(sample_pdf, "", "owner1234", tmp_path / "out")
    with pytest.raises(ValidationError):
        security.encrypt_pdf(sample_pdf, "user1234", "", tmp_path / "out")


def test_encrypt_short_password_rejected(sample_pdf, tmp_path):
    with pytest.raises(ValidationError):
        security.encrypt_pdf(sample_pdf, "abc", "owner1234", tmp_path / "out")


def test_encrypt_invalid_algorithm_rejected(sample_pdf, tmp_path):
    with pytest.raises(ValidationError):
        security.encrypt_pdf(sample_pdf, "user1234", "owner1234", tmp_path / "out", algorithm="DES")


def test_decrypt_roundtrip_with_known_password(sample_pdf, tmp_path):
    enc = security.encrypt_pdf(sample_pdf, "user1234", "owner1234", tmp_path / "enc")
    dec = security.decrypt_pdf(enc.output, "user1234", tmp_path / "dec")
    assert dec.is_encrypted is False
    state = _state(dec.output)
    assert state["needs_pass"] is False
    assert state["encrypted"] is False
    assert state["pages"] == 5
    assert read_page_texts(dec.output) == read_page_texts(sample_pdf)


def test_decrypt_wrong_password_rejected(sample_pdf, tmp_path):
    enc = security.encrypt_pdf(sample_pdf, "user1234", "owner1234", tmp_path / "enc")
    with pytest.raises(PasswordError) as exc:
        security.decrypt_pdf(enc.output, "salah-pass", tmp_path / "dec")
    assert "user1234" not in str(exc.value)
    assert "salah-pass" not in str(exc.value)


def test_decrypt_on_unencrypted_pdf_rejected(sample_pdf, tmp_path):
    with pytest.raises(ValidationError):
        security.decrypt_pdf(sample_pdf, "user1234", tmp_path / "dec")


def test_passwords_never_in_output_filenames(sample_pdf, tmp_path):
    enc = security.encrypt_pdf(sample_pdf, "user1234", "owner1234", tmp_path / "enc")
    assert "user1234" not in enc.output.name
    dec = security.decrypt_pdf(enc.output, "user1234", tmp_path / "dec")
    assert "user1234" not in dec.output.name


def test_encrypt_source_untouched(sample_pdf, tmp_path):
    before = sample_pdf.read_bytes()
    security.encrypt_pdf(sample_pdf, "user1234", "owner1234", tmp_path / "out")
    assert sample_pdf.read_bytes() == before