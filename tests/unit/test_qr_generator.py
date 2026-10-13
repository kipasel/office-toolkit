"""Unit tests for QR design validation and image building (C1-C3)."""

import pytest

from office_toolkit.core.errors import ValidationError
from office_toolkit.services.qr import generator as gen
from office_toolkit.services.qr.generator import QrDesign, build_qr_image, validate_design
from office_toolkit.services.qr.common import MIN_CONTRAST_RATIO


def test_default_design_is_valid():
    assert validate_design(QrDesign()) == []


def test_empty_data_rejected():
    with pytest.raises(ValidationError):
        build_qr_image("   ", QrDesign())


def test_data_too_long_rejected():
    with pytest.raises(ValidationError, match="terlalu panjang"):
        build_qr_image("X" * 5000, QrDesign())


def test_unicode_and_url_data_accepted():
    img, warn = build_qr_image("Harga \u20ac 100% \u2014 https://contoh.id/a?b=1", QrDesign())
    assert img.size[0] > 0
    assert warn == []


def test_box_size_zero_rejected():
    with pytest.raises(ValidationError):
        validate_design(QrDesign(box_size=0))


def test_negative_quiet_zone_rejected():
    with pytest.raises(ValidationError):
        validate_design(QrDesign(border=-1))


def test_small_quiet_zone_warns():
    warn = validate_design(QrDesign(border=1))
    assert any("Quiet zone kecil" in w for w in warn)


def test_invalid_color_format_rejected():
    with pytest.raises(ValidationError, match="RRGGBB"):
        validate_design(QrDesign(fg_color="darkblue"))


def test_low_contrast_warns():
    warn = validate_design(QrDesign(fg_color="#0000FF", bg_color="#000000"))
    assert any("Kontras" in w for w in warn)


def test_high_contrast_no_warning():
    warn = validate_design(QrDesign(fg_color="#000000", bg_color="#FFFFFF"))
    assert not any("Kontras" in w for w in warn)


def test_invalid_ecc_rejected():
    with pytest.raises(ValidationError, match="Error correction"):
        validate_design(QrDesign(error_correction="Z"))


def test_logo_fraction_out_of_range_rejected(tmp_path):
    from fixtures.qr_factory import make_logo

    logo = make_logo(tmp_path / "logo.png")
    with pytest.raises(ValidationError):
        validate_design(QrDesign(logo_path=logo, logo_fraction=0.9))
    with pytest.raises(ValidationError):
        validate_design(QrDesign(logo_path=logo, logo_fraction=0.0))


def test_contrast_ratio_sanity():
    from office_toolkit.services.qr.common import contrast_ratio, hex_to_rgb

    r = contrast_ratio(hex_to_rgb("#000000"), hex_to_rgb("#FFFFFF"))
    assert round(r, 1) >= MIN_CONTRAST_RATIO


def test_higher_ecc_produces_larger_image():
    base, _ = build_qr_image("data-ECC", QrDesign(error_correction="L"))
    high, _ = build_qr_image("data-ECC", QrDesign(error_correction="H"))
    assert high.size[0] >= base.size[0]