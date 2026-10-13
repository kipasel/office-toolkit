"""Security/privacy tests for QR services: traversal, overwrite, source safety,
payload non-logging, input limits, and temp-file hygiene."""

from dataclasses import replace
from pathlib import Path

import pytest

from office_toolkit.core.config import _CONFIG, AppConfig, get_config
from office_toolkit.core.errors import ResourceLimitError
from office_toolkit.services.qr import csv_batch
from office_toolkit.services.qr.decoder import decode_qr
from office_toolkit.services.qr.generator import QrDesign, render_qr_png
from fixtures.qr_factory import make_csv, make_qr_image


@pytest.fixture
def patched_config(monkeypatch):
    def _apply(**kw):
        monkeypatch.setattr("office_toolkit.core.config._CONFIG", replace(get_config(), **kw))
        return get_config()

    return _apply


def test_path_traversal_via_csv_filename_blocked(tmp_path):
    csv_path = make_csv(tmp_path / "t.csv", ["isi", "nama"], [["1", "../keluar"]])
    res = csv_batch.process_csv_batch(csv_path, tmp_path / "out", "isi", filename_column="nama")
    assert len(res.succeeded) == 1
    out_dir = tmp_path / "out"
    for p in res.succeeded:
        assert p.resolve().parent == out_dir.resolve()
        names = [x.name for x in out_dir.iterdir()]
        assert "keluar.png" not in names


def test_batch_never_overwrites_existing_file(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "jd.png").write_bytes(b"existing")
    csv_path = make_csv(tmp_path / "o.csv", ["isi", "nama"], [["1", "jd"]])
    res = csv_batch.process_csv_batch(csv_path, out_dir, "isi", filename_column="nama")
    assert [p.name for p in res.succeeded] == ["jd_1.png"]
    assert (out_dir / "jd.png").read_bytes() == b"existing"


def test_single_export_never_overwrites(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "s.png").write_bytes(b"old")
    res = render_qr_png("data", out_dir, output_name="s")
    assert res.output.name == "s_1.png"
    assert (out_dir / "s.png").read_bytes() == b"old"


def test_source_csv_never_modified(tmp_path):
    csv_path = make_csv(tmp_path / "src.csv", ["isi", "nama"], [["1", "a"], ["2", "b"]])
    before = csv_path.read_bytes()
    csv_batch.process_csv_batch(csv_path, tmp_path / "out", "isi", filename_column="nama")
    assert csv_path.read_bytes() == before


def test_source_image_never_modified(tmp_path):
    img = make_qr_image(tmp_path / "src.png", "RAHASIA-422")
    before = img.read_bytes()
    res = decode_qr(img)
    assert res.found
    assert img.read_bytes() == before


def test_payload_never_logged(tmp_path, caplog):
    payload = "KODE-SUPER-RAHASIA-7821"
    out_dir = tmp_path / "out"
    with caplog.at_level("DEBUG"):
        img_path = make_qr_image(tmp_path / "q.png", payload)
        render_qr_png(payload, out_dir)
        res = decode_qr(img_path)
        assert res.found
    assert payload not in caplog.text


def test_no_temp_files_left(tmp_path):
    d = tmp_path / "out"
    render_qr_png("data", d)
    csv_path = make_csv(tmp_path / "c.csv", ["isi"], [["1"], ["2"]])
    csv_batch.process_csv_batch(csv_path, d, "isi")
    leftovers = [p for p in Path(d).iterdir() if p.name.startswith("otk_")]
    assert leftovers == []


def test_input_size_limit_decode(patched_config, tmp_path):
    patched_config(max_input_mb=0)
    img = make_qr_image(tmp_path / "q.png", "data")
    with pytest.raises(ResourceLimitError, match="[Uu]kuran file"):
        decode_qr(img)


def test_input_size_limit_csv(patched_config, tmp_path):
    patched_config(max_input_mb=0)
    csv_path = make_csv(tmp_path / "c.csv", ["isi"], [["1"]])
    with pytest.raises(ResourceLimitError, match="[Uu]kuran file"):
        csv_batch.read_csv_rows(csv_path)


def test_decode_returns_url_payload_as_plain_text(tmp_path):
    # A URL payload must come back as ordinary text; the decoder never opens a
    # browser and never dials out (no cloud/network code path exists).
    payload = "https://contoh.id/aman?token=1"
    img = make_qr_image(tmp_path / "u.png", payload)
    res = decode_qr(img)
    assert res.items[0].text == payload
    assert res.found