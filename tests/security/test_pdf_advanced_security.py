"""Security-focused tests for advanced PDF features (no real documents)."""

import hashlib
import logging

import pymupdf
from PIL import Image

import pytest

from office_toolkit.core.errors import ResourceLimitError
from office_toolkit.services.pdf import compress, edit, from_images, render, security


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_sources_never_modified(pdf_factory, tmp_path):
    src = pdf_factory.make_pdf_with_image(tmp_path / "s.pdf", ["G1"])
    img = tmp_path / "logo.png"
    Image.new("RGBA", (40, 20), "red").save(img)
    before_src = _sha256(src)
    before_img = _sha256(img)
    compress.compress_pdf(src, tmp_path / "c", "images")
    render.render_pdf_to_images(src, tmp_path / "r")
    edit.add_text_to_pdf(src, "teks", "1", tmp_path / "t")
    edit.add_image_to_pdf(src, img, "1", tmp_path / "i")
    from_images.images_to_pdf([img], tmp_path / "f")
    enc = security.encrypt_pdf(src, "user1234", "owner1234", tmp_path / "e")
    security.decrypt_pdf(enc.output, "user1234", tmp_path / "d")
    assert _sha256(src) == before_src
    assert _sha256(img) == before_img


def test_no_temp_leftover_after_failure(corrupt_pdf, tmp_path):
    out_dir = tmp_path / "out"
    for func in (
        lambda: compress.compress_pdf(corrupt_pdf, out_dir, "struktur"),
        lambda: render.render_pdf_to_images(corrupt_pdf, out_dir),
    ):
        with pytest.raises(Exception):
            func()
    leftovers = list(out_dir.glob("otk_*")) if out_dir.exists() else []
    assert leftovers == []


def test_password_never_reaches_logs(sample_pdf, tmp_path, caplog):
    secret = "Rahasia-Sangat-2026"
    with caplog.at_level(logging.INFO):
        enc = security.encrypt_pdf(sample_pdf, secret, "Pemilik-2026", tmp_path / "e")
        security.decrypt_pdf(enc.output, secret, tmp_path / "d")
    assert secret not in caplog.text
    assert "Pemilik-2026" not in caplog.text


def test_encrypt_illegal_output_name_sanitized(sample_pdf, tmp_path):
    res = security.encrypt_pdf(
        sample_pdf, "user1234", "owner1234", tmp_path / "out",
        output_name="bad:na*me?.pdf",
    )
    for ch in ':*?':
        assert ch not in res.output.name


def test_render_dpi_limit_is_config_driven(sample_pdf, tmp_path, monkeypatch):
    from office_toolkit.core.config import AppConfig
    from office_toolkit.services.pdf import common

    cfg = AppConfig(pdf_render_dpi_max=50)
    monkeypatch.setattr(common, "get_config", lambda: cfg)
    from office_toolkit.core.errors import ValidationError

    with pytest.raises(ValidationError):
        render.render_pdf_to_images(sample_pdf, tmp_path / "out", pages="1", dpi=72)
    res = render.render_pdf_to_images(sample_pdf, tmp_path / "out", pages="1", dpi=36)
    assert res.rendered_count == 1


def test_images_to_pdf_pixel_limit_enforced(pdf_factory, tmp_path, monkeypatch):
    from office_toolkit.core.config import AppConfig

    img = tmp_path / "big.png"
    Image.new("RGB", (5000, 5000), "red").save(img, compression_level=9)
    monkeypatch.setattr(from_images, "get_config", lambda: AppConfig(max_image_pixels=100))
    from office_toolkit.core.errors import ResourceLimitError

    with pytest.raises(ResourceLimitError):
        from_images.images_to_pdf([img], tmp_path / "out")


def test_compression_never_modifies_input_on_failure(pdf_factory, tmp_path):
    src = pdf_factory.make_pdf(tmp_path / "s.pdf", ["A"])
    before = _sha256(src)
    with pytest.raises(Exception):
        compress.compress_pdf(src, tmp_path / "out", "images", quality=101)
    assert _sha256(src) == before


def test_encrypted_pdf_rejected_for_operations(encrypted_pdf, tmp_path):
    from office_toolkit.core.errors import PasswordError

    for func in (
        lambda: render.render_pdf_to_images(encrypted_pdf, tmp_path / "r"),
        lambda: compress.compress_pdf(encrypted_pdf, tmp_path / "c"),
        lambda: edit.add_text_to_pdf(encrypted_pdf, "x", "1", tmp_path / "t"),
    ):
        with pytest.raises(PasswordError):
            func()