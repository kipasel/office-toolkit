"""Unit tests for CSV batch QR generation (C5)."""

from dataclasses import replace

import pytest

from office_toolkit.core.config import _CONFIG, AppConfig, get_config
from office_toolkit.core.errors import ResourceLimitError, ValidationError
from office_toolkit.services.qr import csv_batch
from office_toolkit.services.qr.decoder import decode_qr
from fixtures.qr_factory import make_csv


@pytest.fixture
def patched_config(monkeypatch):
    def _apply(**kw):
        monkeypatch.setattr("office_toolkit.core.config._CONFIG", replace(get_config(), **kw))
        return get_config()

    return _apply


def test_read_bom_and_no_bom(tmp_path):
    a = make_csv(tmp_path / "a.csv", ["isi", "nama"], [["p1", "f1"], ["p2", "f2"]], bom=True)
    b = make_csv(tmp_path / "b.csv", ["isi"], [["p3"]], bom=False)
    for f in (a, b):
        header, rows, lines = csv_batch.read_csv_rows(f)
        assert header == ["isi", "nama"] or header == ["isi"]
        assert lines == list(range(2, 2 + len(rows)))


def test_blank_rows_and_cells_handled(tmp_path):
    csv_path = make_csv(tmp_path / "m.csv", ["isi", "nama"], [["", "f1"], ["p2"], [], ["p4", "f4"]])
    header, rows, lines = csv_batch.read_csv_rows(csv_path)
    assert len(rows) == 3  # blank row dropped, blank cell kept
    assert lines == [2, 3, 5]


def test_empty_file_rejected(tmp_path):
    empty = tmp_path / "e.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValidationError):  # File kosong / CSV kosong
        csv_batch.read_csv_rows(empty)


def test_duplicate_header_rejected(tmp_path):
    csv_path = make_csv(tmp_path / "d.csv", ["x", "x"], [["1", "2"]])
    with pytest.raises(ValidationError, match="duplikat"):
        csv_batch.read_csv_rows(csv_path)


def test_blank_header_line_rejected(tmp_path):
    blank_first = tmp_path / "bf.csv"
    blank_first.write_text("\nisi\n1\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="Header"):
        csv_batch.read_csv_rows(blank_first)


def test_non_utf8_rejected(tmp_path):
    latin = tmp_path / "latin.csv"
    latin.write_bytes("caf\xe9".encode("latin-1"))  # non-ASCII latin-1 byte \xe9
    with pytest.raises(ValidationError, match="UTF-8"):
        csv_batch.read_csv_rows(latin)


def test_max_rows_limit(patched_config, tmp_path):
    patched_config(max_csv_batch_rows=2)
    csv_path = make_csv(tmp_path / "big.csv", ["isi"], [["1"], ["2"], ["3"]])
    with pytest.raises(ResourceLimitError):
        csv_batch.read_csv_rows(csv_path)


def test_batch_png_success_and_decode(tmp_path):
    csv_path = make_csv(
        tmp_path / "b.csv",
        ["isi", "nama"],
        [["https://contoh.id/a", "berkasA"], ["https://contoh.id/b", "berkasB"]],
    )
    res = csv_batch.process_csv_batch(csv_path, tmp_path / "out", "isi", filename_column="nama")
    assert res.fmt == "png"
    assert len(res.succeeded) == 2
    assert res.failed == []
    assert res.total_rows == 2
    names = {p.name for p in res.succeeded}
    assert names == {"berkasA.png", "berkasB.png"}
    decoded = dict(
        (p.name, decode_qr(p).items[0].text) for p in res.succeeded
    )
    assert decoded["berkasA.png"] == "https://contoh.id/a"
    assert decoded["berkasB.png"] == "https://contoh.id/b"


def test_batch_autoname_fallback(tmp_path):
    csv_path = make_csv(tmp_path / "n.csv", ["isi"], [["A"], ["B"]])
    res = csv_batch.process_csv_batch(csv_path, tmp_path / "out", "isi")
    assert [p.name for p in res.succeeded] == ["qr_0001.png", "qr_0002.png"]


def test_batch_empty_content_cell_fails_per_line(tmp_path):
    csv_path = make_csv(tmp_path / "o.csv", ["isi", "nama"], [["", "f1"], ["ok", "f2"]])
    res = csv_batch.process_csv_batch(csv_path, tmp_path / "out", "isi", filename_column="nama")
    assert len(res.succeeded) == 1
    assert res.failed == [(2, "Kolom konten kosong.")]
    assert res.skipped_rows == 0


def test_batch_missing_column_rejected(tmp_path):
    csv_path = make_csv(tmp_path / "c.csv", ["isi"], [["1"]])
    with pytest.raises(ValidationError, match="tidak ada"):
        csv_batch.process_csv_batch(csv_path, tmp_path / "out", "tidak_ada")


def test_batch_svg_success(tmp_path):
    csv_path = make_csv(tmp_path / "s.csv", ["isi"], [["svgsatu"], ["svgdua"]])
    res = csv_batch.process_csv_batch(csv_path, tmp_path / "out", "isi", fmt="svg")
    assert [p.suffix for p in res.succeeded] == [".svg", ".svg"]


def test_batch_svg_with_logo_rejected(tmp_path):
    from office_toolkit.services.qr.generator import QrDesign
    from fixtures.qr_factory import make_logo

    logo = make_logo(tmp_path / "logo.png")
    csv_path = make_csv(tmp_path / "l.csv", ["isi"], [["1"]])
    with pytest.raises(ValidationError, match="SVG"):
        csv_batch.process_csv_batch(
            csv_path, tmp_path / "out", "isi", fmt="svg", design=QrDesign(logo_path=logo)
        )


def test_batch_progress_callback(tmp_path):
    csv_path = make_csv(tmp_path / "p.csv", ["isi"], [["1"], ["2"], ["3"]])
    calls = []
    csv_batch.process_csv_batch(
        csv_path, tmp_path / "out", "isi", progress_cb=lambda c, t: calls.append((c, t))
    )
    assert calls == [(1, 3), (2, 3), (3, 3)]


def test_batch_duplicate_names_do_not_overwrite(tmp_path):
    csv_path = make_csv(tmp_path / "d.csv", ["isi", "nama"], [["1", "sama"], ["2", "sama"]])
    res = csv_batch.process_csv_batch(csv_path, tmp_path / "out", "isi", filename_column="nama")
    assert len(res.succeeded) == 2
    names = sorted(p.name for p in res.succeeded)
    assert names == ["sama.png", "sama_1.png"]


def test_batch_progress_reports_total(tmp_path):
    csv_path = make_csv(tmp_path / "q.csv", ["isi"], [["1"]])
    res = csv_batch.process_csv_batch(csv_path, tmp_path / "out", "isi")
    assert res.skipped_rows == 0
    assert len(res.succeeded) + len(res.failed) == res.total_rows


def test_preview_csv_returns_header_and_rows(tmp_path):
    csv_path = make_csv(
        tmp_path / "pv.csv", ["isi", "nama"], [["1", "a"], ["2", "b"], ["3", "c"]]
    )
    header, preview = csv_batch.preview_csv(csv_path, max_preview=2)
    assert header == ["isi", "nama"]
    assert len(preview) == 2