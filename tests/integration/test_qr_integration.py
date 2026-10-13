"""Integration tests: QR generate -> decode round trip through the Qt worker."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from office_toolkit.core.job_manager import JobManager, JobResult
from office_toolkit.services.qr import csv_batch
from office_toolkit.services.qr.decoder import decode_qr
from office_toolkit.services.qr.generator import QrDesign, render_qr_png
from fixtures.qr_factory import make_csv, make_logo


@pytest.fixture
def app():
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    return qapp


def _run_job(jm: JobManager, func, timeout_ms: int = 30000) -> JobResult:
    holder = {}
    loop = QEventLoop()

    def on_finished(jid, res):
        holder["res"] = res
        loop.quit()

    jm.job_finished.connect(on_finished)
    QTimer.singleShot(timeout_ms, loop.quit)
    jm.start_job(func)
    loop.exec()
    try:
        jm.job_finished.disconnect(on_finished)
    except (RuntimeError, TypeError):
        pass
    return holder.get("res")


def test_worker_generate_to_decode_roundtrip(app, tmp_path):
    payload = "https://contoh.id/berkas?hal=1"
    out_dir = tmp_path / "out"
    jm = JobManager()
    gen_result = _run_job(jm, lambda: _gen(payload, out_dir))
    assert gen_result is not None and gen_result.success
    path = gen_result.data["path"]

    dec_result = _run_job(jm, lambda: _decode(path))
    assert dec_result is not None and dec_result.success
    assert dec_result.data["text"] == payload


def test_worker_batch_then_decode_all(app, tmp_path):
    csv_path = make_csv(
        tmp_path / "b.csv",
        ["isi", "nama"],
        [["Isi-A", "a"], ["Isi-B", "b"], ["Isi-C", "c"]],
    )
    out_dir = tmp_path / "out"
    jm = JobManager()
    batch = _run_job(jm, lambda: _batch(csv_path, out_dir))
    assert batch is not None and batch.success
    assert batch.data["ok"] == 3

    for p in out_dir.iterdir():
        if p.suffix == ".png":
            dec = _run_job(jm, lambda pp=p: _decode(pp))
            assert dec is not None and dec.success
            assert dec.data["text"].startswith("Isi-")


def test_worker_logo_roundtrip(app, tmp_path):
    logo = make_logo(tmp_path / "logo.png", size=48)
    out_dir = tmp_path / "out"
    jm = JobManager()
    gen = _run_job(
        jm, lambda: _gen(
            "LOGO-INTEGRASI-77", out_dir, design=QrDesign(logo_path=logo, error_correction="H")
        )
    )
    assert gen is not None and gen.success
    dec = _run_job(jm, lambda: _decode(gen.data["path"]))
    assert dec.data["text"] == "LOGO-INTEGRASI-77"


def test_worker_failure_propagates_error(app, tmp_path):
    jm = JobManager()
    result = _run_job(jm, lambda: _gen("", tmp_path / "out"))
    assert result is not None
    assert result.success is False
    assert result.error


def _gen(payload, out_dir, design=None) -> JobResult:
    if not payload.strip():
        return JobResult(
            success=False, error="Isi data QR tidak boleh kosong."
        )
    res = render_qr_png(payload, out_dir, design=design)
    return JobResult(success=True, data={"path": res.output})


def _decode(path) -> JobResult:
    res = decode_qr(path)
    if not res.found:
        return JobResult(success=False, error="QR tidak ditemukan")
    return JobResult(success=True, data={"text": res.items[0].text})


def _batch(csv_path, out_dir) -> JobResult:
    res = csv_batch.process_csv_batch(csv_path, out_dir, "isi", filename_column="nama")
    return JobResult(success=True, data={"ok": len(res.succeeded), "fail": len(res.failed)})