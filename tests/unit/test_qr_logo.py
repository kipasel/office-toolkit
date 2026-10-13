"""Unit tests for logo overlay on QR codes (C3 logo feature)."""

import pytest

from office_toolkit.core.errors import ValidationError
from office_toolkit.services.qr.generator import QrDesign, build_qr_image, render_qr_png
from office_toolkit.services.qr.decoder import decode_qr
from fixtures.qr_factory import make_logo


def test_logo_overlay_warns(tmp_path):
    logo = make_logo(tmp_path / "logo.png")
    img, warn = build_qr_image("data-dengan-logo", QrDesign(logo_path=logo, error_correction="H"))
    assert any("Logo" in w for w in warn)


def test_logo_changes_pixel_content(tmp_path):
    logo = make_logo(tmp_path / "logo.png", color=(200, 40, 40))
    plain, _ = build_qr_image("satu-dua-tiga", QrDesign(error_correction="H"))
    with_logo, _ = build_qr_image("satu-dua-tiga", QrDesign(logo_path=logo, error_correction="H"))
    assert list(with_logo.size) == list(plain.size)
    assert with_logo.tobytes() != plain.tobytes()


def test_logo_exported_png_still_decodes(tmp_path):
    logo = make_logo(tmp_path / "logo.png", size=48, color=(180, 30, 30))
    payload = "LOGO-ROUNDTRIP-9281"
    res = render_qr_png(
        payload,
        tmp_path / "out",
        design=QrDesign(logo_path=logo, error_correction="H", box_size=10),
    )
    decoded = decode_qr(res.output)
    assert decoded.found is True
    assert decoded.items[0].text == payload


def test_missing_logo_file_rejected(tmp_path):
    with pytest.raises(ValidationError):
        build_qr_image("data", QrDesign(logo_path=tmp_path / "tidak_ada.png"))


def test_non_image_logo_rejected(tmp_path,):
    bogus = tmp_path / "bogus.png"
    bogus.write_bytes(b"not an image at all")
    with pytest.raises(ValidationError):
        build_qr_image("data", QrDesign(logo_path=bogus))


def test_logo_fraction_limits_size(tmp_path):
    logo = make_logo(tmp_path / "logo.png", size=100)
    img, _ = build_qr_image("data", QrDesign(logo_path=logo, logo_fraction=0.05, error_correction="H"))
    # the overlaid logo must be strictly smaller than the QR itself
    assert img.size[0] > 60 * 0.05 * 2