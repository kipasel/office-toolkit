"""Unit tests for QR decoding (C6)."""

import time
from dataclasses import replace
from pathlib import Path

import cv2
import pytest
from PIL import Image

from office_toolkit.core.config import _CONFIG, AppConfig, get_config
from office_toolkit.core.errors import DecodeError, ResourceLimitError, ValidationError
from office_toolkit.services.qr.decoder import decode_qr
from fixtures.qr_factory import make_corrupt_image, make_plain_image, make_qr_image


@pytest.fixture
def patched_config(monkeypatch):
    def _apply(**kw):
        monkeypatch.setattr("office_toolkit.core.config._CONFIG", replace(get_config(), **kw))
        return get_config()

    return _apply


def test_decode_simple_roundtrip(tmp_path):
    img = make_qr_image(tmp_path / "q.png", "https://contoh.id/x?m=1&n=2")
    res = decode_qr(img)
    assert res.found is True
    assert res.items[0].text == "https://contoh.id/x?m=1&n=2"


def _concat_qrs(tmp_path, left_data, right_data, box_size=8) -> Path:
    left = make_qr_image(tmp_path / "left.png", left_data, box_size=box_size)
    right = make_qr_image(tmp_path / "right.png", right_data, box_size=box_size)
    lw, lh = Image.open(left).size
    rw, rh = Image.open(right).size
    canvas = Image.new("RGB", (lw + rw + 40, max(lh, rh)), "white")
    canvas.paste(Image.open(left), (0, 0))
    canvas.paste(Image.open(right), (lw + 40, 0))
    both = tmp_path / "both.png"
    canvas.save(both)
    return both


def test_decode_multiple_qrs(tmp_path):
    both = _concat_qrs(tmp_path, "KIRI-111", "KANAN-222")

    res = decode_qr(both)
    assert res.found is True
    texts = {it.text for it in res.items}
    assert "KIRI-111" in texts and "KANAN-222" in texts


def test_decode_max_items(tmp_path):
    both = _concat_qrs(tmp_path, "KIRI-111", "KANAN-222")

    res = decode_qr(both, max_items=1)
    assert len(res.items) == 1


def test_decode_no_qr_returns_not_found(tmp_path):
    img = make_plain_image(tmp_path / "plain.png")
    res = decode_qr(img)
    assert res.found is False
    assert res.items == []


def test_decode_corrupt_image_raises(tmp_path):
    img = make_corrupt_image(tmp_path / "broken.png")
    with pytest.raises(DecodeError):
        decode_qr(img)


def test_decode_missing_file_raises(tmp_path):
    with pytest.raises(ValidationError):
        decode_qr(tmp_path / "missing.png")


def test_decode_payloads_are_not_truncated(tmp_path):
    payload = "NOMOR-000123-" + "x" * 40
    img = make_qr_image(tmp_path / "long.png", payload)
    res = decode_qr(img)
    assert res.found
    assert res.items[0].text == payload


def test_decode_pixel_limit(patched_config, tmp_path):
    patched_config(max_image_pixels=100)
    img = make_qr_image(tmp_path / "big.png", "data", box_size=10)
    with pytest.raises(ResourceLimitError, match="piksel"):
        decode_qr(img)


def test_decode_timeout(patched_config, monkeypatch, tmp_path):
    patched_config(qr_decode_timeout_sec=1)
    img = make_qr_image(tmp_path / "t.png", "data")

    def slow_detect(self, img):
        time.sleep(3)
        return (False, None, None, None)

    monkeypatch.setattr(cv2.QRCodeDetector, "detectAndDecodeMulti", slow_detect)
    with pytest.raises(ResourceLimitError, match="waktu batas"):
        decode_qr(img)


def test_scan_with_no_qr_is_never_timeout(tmp_path):
    img = make_plain_image(tmp_path / "n.png", size=300)
    res = decode_qr(img)
    assert res.found is False