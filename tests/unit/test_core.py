import os
import tempfile
from pathlib import Path

import pytest

from office_toolkit.core import file_validation, output_manager, config, errors


def test_config_defaults():
    c = config.AppConfig()
    assert c.max_input_mb == 500
    assert c.max_image_pixels == 100_000_000
    assert c.max_pdf_pages_render == 5000
    assert c.qr_decode_timeout_sec == 30
    assert c.max_csv_batch_rows == 100000


def test_validate_input_file_not_exists():
    res = file_validation.validate_input_file("no_such_file_xyz.txt")
    assert not res.valid


def test_validate_input_file_empty(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_bytes(b"")
    res = file_validation.validate_input_file(f)
    assert not res.valid


def test_validate_output_dir_creates(tmp_path):
    d = tmp_path / "out_test"
    res = file_validation.validate_output_dir(d)
    assert res.valid
    assert d.exists()


def test_ensure_no_conflict_block(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    res = file_validation.ensure_no_conflict(f, allow_overwrite=False)
    assert not res.valid


def test_ensure_no_conflict_allow(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    res = file_validation.ensure_no_conflict(f, allow_overwrite=True)
    assert res.valid


def test_output_manager_safe_path_conflict(tmp_path):
    om = output_manager.OutputManager(default_dir=tmp_path)
    f = tmp_path / "out.txt"
    f.write_text("x")
    alt = om.safe_output_path("out.txt", dir_path=tmp_path, allow_overwrite=False)
    assert alt.name != "out.txt"
    assert alt.parent == tmp_path


def test_output_manager_sanitize(tmp_path):
    om = output_manager.OutputManager(default_dir=tmp_path)
    p = om.safe_output_path("bad:na*me?.txt", dir_path=tmp_path)
    assert "<" not in p.name and ":" not in p.name


def test_output_manager_cleanup(tmp_path):
    om = output_manager.OutputManager(default_dir=tmp_path)
    tmpf = om.write_temp_in_dir(tmp_path, suffix=".tmp")
    assert tmpf.exists()
    om.cleanup(tmpf)
    assert not tmpf.exists()


def test_logging_no_secret_leak(tmp_path, monkeypatch):
    from office_toolkit.core import logging_config
    c = config.AppConfig()
    # ensure dirs not needed; use tmp logs
    log = tmp_path / "test.log"
    logger = logging_config.setup_logging(c, log_file=str(log))
    logger.info("test message")
    content = log.read_text(encoding="utf-8", errors="ignore")
    assert "secret" not in content
    assert "password" not in content
