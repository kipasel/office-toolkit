"""Integration tests: PDF operations through the Qt worker (JobManager)."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from office_toolkit.core.job_manager import JobManager, JobResult
from office_toolkit.services.pdf import processor
from fixtures.pdf_factory import page_count, read_page_texts


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


def test_worker_merge_then_split_roundtrip(app, tmp_path, pdf_factory):
    a = pdf_factory.make_pdf(tmp_path / "a.pdf", ["A1", "A2"])
    b = pdf_factory.make_pdf(tmp_path / "b.pdf", ["B1"])
    out_dir = tmp_path / "merged"

    jm = JobManager()
    merged_result = _run_job(jm, lambda: _merge(a, b, out_dir))
    assert merged_result is not None and merged_result.success
    merged_path = merged_result.data["path"]
    assert page_count(merged_path) == 3
    assert read_page_texts(merged_path) == ["A1", "A2", "B1"]

    split_dir = tmp_path / "split"
    split_result = _run_job(jm, lambda: _split_each(merged_path, split_dir))
    assert split_result is not None and split_result.success
    assert split_result.data["count"] == 3


def test_worker_reports_failure(app, tmp_path, pdf_factory):
    a = pdf_factory.make_pdf(tmp_path / "a.pdf", ["A1"])

    jm = JobManager()
    result = _run_job(jm, lambda: _merge(a, tmp_path / "b_missing.pdf", tmp_path / "out"))
    assert result is not None
    assert result.success is False
    assert result.error


def _merge(a, b, out_dir) -> JobResult:
    res = processor.merge_pdfs([a, b], out_dir)
    return JobResult(success=True, data={"path": res.output, "pages": res.page_count})


def _split_each(path, out_dir) -> JobResult:
    res = processor.split_each_page(path, out_dir)
    return JobResult(success=True, data={"count": len(res.outputs)})
