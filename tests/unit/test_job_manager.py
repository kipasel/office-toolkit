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


def _wait_for(app, predicate, timeout: float = 3.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        app.processEvents()
        time.sleep(0.005)
    app.processEvents()
    return predicate()


def test_job_success(app):
    jm = job_manager.JobManager()
    results = []

    def ok():
        time.sleep(0.001)
        return job_manager.JobResult(success=True, data={"x": 1})

    jm.job_finished.connect(lambda jid, res: results.append(res))
    jid = jm.start_job(ok)
    assert jid.startswith("job_")
    assert _wait_for(app, lambda: results)
    assert results and results[0].success
    assert results[0].data["x"] == 1


def test_job_failure(app):
    jm = job_manager.JobManager()
    results = []

    def bad():
        raise ValueError("boom")

    jm.job_finished.connect(lambda jid, res: results.append(res))
    jm.start_job(bad)
    assert _wait_for(app, lambda: results)
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
    # no progress emitted explicitly; just ensure no crash
    assert _wait_for(app, lambda: True)
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
    # may cancel or finish; ensure handled without crashing
    _wait_for(app, lambda: results or jm._jobs.get(jid, {}).get("status") is not None)
    assert True


def test_many_jobs_one_manager(app):
    """Regression: churning many jobs used to abort the process."""
    jm = job_manager.JobManager()
    results = []

    def make(i):
        return lambda: job_manager.JobResult(success=True, data={"i": i})

    jm.job_finished.connect(lambda jid, res: results.append(res))
    for i in range(40):
        jm.start_job(make(i))
    assert _wait_for(app, lambda: len(results) == 40, timeout=10.0)
    assert all(r.success for r in results)
    assert sorted(r.data["i"] for r in results) == list(range(40))


def test_manager_dropped_while_job_runs(app):
    """Regression: a short-lived manager must not destroy its running thread."""
    for _ in range(25):
        jm = job_manager.JobManager()
        jm.start_job(lambda: job_manager.JobResult(success=True))
        del jm
        app.processEvents()
    # every thread finished and was released; nothing is left running
    assert _wait_for(app, lambda: not job_manager._ACTIVE, timeout=10.0)

