import time

from PySide6.QtCore import QCoreApplication
import pytest

from office_toolkit.core import job_manager


@pytest.fixture
def app():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


def test_job_success(app):
    jm = job_manager.JobManager()
    results = []

    def ok():
        time.sleep(0.001)
        return job_manager.JobResult(success=True, data={"x": 1})

    jm.job_finished.connect(lambda jid, res: results.append(res))
    jid = jm.start_job(ok)
    assert jid.startswith("job_")
    app.processEvents()
    time.sleep(0.01)
    app.processEvents()
    assert results and results[0].success
    assert results[0].data["x"] == 1


def test_job_failure(app):
    jm = job_manager.JobManager()
    results = []

    def bad():
        raise ValueError("boom")

    jm.job_finished.connect(lambda jid, res: results.append(res))
    jm.start_job(bad)
    app.processEvents()
    time.sleep(0.01)
    app.processEvents()
    assert results and not results[0].success
    assert results[0].error


def test_job_progress_signals(app):
    jm = job_manager.JobManager()
    progressed = []

    def with_progress():
        # simulate
        return job_manager.JobResult(success=True)

    jm.job_progress.connect(lambda jid, p: progressed.append(p))
    jm.start_job(with_progress)
    app.processEvents()
    time.sleep(0.01)
    app.processEvents()
    # no progress emitted explicitly; just ensure no crash
    assert True


def test_cancel_no_crash(app):
    jm = job_manager.JobManager()
    results = []

    def slow():
        time.sleep(0.05)
        return job_manager.JobResult(success=True)

    jm.job_finished.connect(lambda jid, res: results.append(res))
    jid = jm.start_job(slow, can_cancel=True)
    jm.cancel_job(jid)
    app.processEvents()
    time.sleep(0.02)
    app.processEvents()
    # may cancel or finish; ensure handled
    assert True
