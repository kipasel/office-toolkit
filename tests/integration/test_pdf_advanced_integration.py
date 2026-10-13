"""Integration tests: advanced PDF features through the Qt worker (JobManager)."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from office_toolkit.core.job_manager import JobManager, JobResult
from office_toolkit.services.pdf import compress, render
from fixtures.pdf_factory import page_count


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


def test_worker_compress_then_render_roundtrip(app, tmp_path, pdf_factory):
    src = pdf_factory.make_pdf_with_image(tmp_path / "s.pdf", ["G1", "G2"])
    jm = JobManager()

    comp_result = _run_job(
        jm, lambda: _compress(src, tmp_path / "compressed")
    )
    assert comp_result is not None and comp_result.success
    comp_path = comp_result.data["path"]
    assert page_count(comp_path) == 2

    render_result = _run_job(
        jm, lambda: _render(comp_path, tmp_path / "images")
    )
    assert render_result is not None and render_result.success
    assert render_result.data["count"] == 2


def test_worker_reports_advanced_failure(app, tmp_path, pdf_factory):
    from office_toolkit.core.errors import PasswordError

    src = pdf_factory.make_pdf(tmp_path / "s.pdf", ["A"])
    from fixtures.pdf_factory import make_encrypted_pdf

    secured = make_encrypted_pdf(tmp_path / "secured.pdf")

    jm = JobManager()
    result = _run_job(jm, lambda: _render(secured, tmp_path / "out"))
    assert result is not None
    assert result.success is False
    assert result.error


def _compress(src, out_dir) -> JobResult:
    res = compress.compress_pdf(src, out_dir, "images", quality=70)
    return JobResult(success=True, data={"path": res.output, "pages": res.page_count})


def _render(path, out_dir) -> JobResult:
    res = render.render_pdf_to_images(path, out_dir, dpi=72)
    return JobResult(success=True, data={"count": res.rendered_count, "path": res.outputs[0].output})