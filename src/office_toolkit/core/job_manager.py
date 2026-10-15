"""Background job execution on Qt threads.

A job runs a blocking callable on a dedicated ``QThread`` and reports back to
the UI (main) thread through ``job_finished`` / ``job_progress`` signals.

Thread lifecycle:

* The worker's completion signals are connected to bound methods of
  ``JobManager`` (which lives on the main thread), so Qt delivers them as queued
  calls on the main thread. Building result/status updates there keeps all
  shared state on one thread.
* ``thread.quit()`` is connected with ``DirectConnection`` so it runs on the
  worker thread the instant the job ends. A queued connection would need a
  running main-thread event loop and leave the thread spinning forever when
  there is none (e.g. a short script or a test that returns without pumping
  events).
* The thread deletes itself once finished. Running (thread, worker) pairs are
  pinned in a module-level registry until then, so a short-lived ``JobManager``
  (or one collected by the garbage collector) can never destroy a still-running
  ``QThread``.

Teardown (``wait``/``deleteLater``) is never performed from inside the worker
thread: calling ``QThread.wait()`` there would wait on the thread from within
itself and abort the process under load.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional
import time

from PySide6.QtCore import QObject, QThread, Qt, Signal


# Keeps running (thread, worker) pairs alive until they finish, independent of
# the owning JobManager's lifetime. Keyed by the QThread object.
_ACTIVE: Dict[QThread, "Worker"] = {}


class _ThreadReaper(QObject):
    """Releases finished threads from the registry on the main thread.

    Connected to ``thread.finished`` so a thread is removed even when its
    JobManager has already been collected (the manager's own handler is gone in
    that case, but this object lives for the process lifetime).
    """

    def handle(self) -> None:
        thread = self.sender()
        if isinstance(thread, QThread):
            _ACTIVE.pop(thread, None)


_reaper = _ThreadReaper()


class JobStatus(Enum):
    QUEUED = auto()
    RUNNING = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class JobResult:
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class Worker(QObject):
    progress = Signal(int)
    started = Signal()
    finished = Signal(object)  # JobResult
    failed = Signal(str)

    def __init__(self, func: Callable[[], JobResult], can_cancel: bool = False,
                 job_id: str = ""):
        super().__init__()
        self._func = func
        self._cancelled = False
        self._can_cancel = can_cancel
        self.job_id = job_id

    def cancel(self) -> None:
        if self._can_cancel:
            self._cancelled = True

    def run(self) -> None:
        try:
            self.started.emit()
            if self._can_cancel and self._cancelled:
                self.finished.emit(JobResult(success=False, error="Dibatalkan"))
                return
            res = self._func()
            if self._can_cancel and self._cancelled and res.success:
                res = JobResult(success=False, error="Dibatalkan")
            self.finished.emit(res)
        except Exception as e:  # reported to the UI, never swallowed
            self.failed.emit(str(e))


class JobManager(QObject):
    job_started = Signal(str)
    job_finished = Signal(str, object)  # id, JobResult
    job_progress = Signal(str, int)

    def __init__(self):
        super().__init__()
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._next_id = 0

    def start_job(self, func: Callable[[], JobResult], can_cancel: bool = False) -> str:
        jid = f"job_{self._next_id}"
        self._next_id += 1
        thread = QThread()
        worker = Worker(func, can_cancel=can_cancel, job_id=jid)
        worker.moveToThread(thread)

        worker.started.connect(self._on_started)
        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)

        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit, Qt.ConnectionType.DirectConnection)
        worker.failed.connect(thread.quit, Qt.ConnectionType.DirectConnection)
        thread.finished.connect(self._on_thread_finished)
        thread.finished.connect(_reaper.handle)

        _ACTIVE[thread] = worker
        self._jobs[jid] = {
            "thread": thread,
            "worker": worker,
            "status": JobStatus.QUEUED,
            "started_at": time.time(),
        }
        thread.start()
        self._jobs[jid]["status"] = JobStatus.RUNNING
        return jid

    def cancel_job(self, jid: str) -> None:
        job = self._jobs.get(jid)
        if not job:
            return
        w: Optional[Worker] = job.get("worker")
        if w is not None:
            w.cancel()
        job["status"] = JobStatus.CANCELLED

    # -- signal handlers (delivered on the main/UI thread) ----------------
    def _on_started(self) -> None:
        worker = self.sender()
        if isinstance(worker, Worker):
            self.job_started.emit(worker.job_id)

    def _on_progress(self, value: int) -> None:
        worker = self.sender()
        if isinstance(worker, Worker):
            self.job_progress.emit(worker.job_id, value)

    def _on_finished(self, res: JobResult) -> None:
        worker = self.sender()
        jid = worker.job_id if isinstance(worker, Worker) else ""
        job = self._jobs.get(jid)
        if job is not None:
            job["status"] = JobStatus.SUCCEEDED if res.success else JobStatus.FAILED
        self.job_finished.emit(jid, res)

    def _on_failed(self, err: str) -> None:
        worker = self.sender()
        jid = worker.job_id if isinstance(worker, Worker) else ""
        job = self._jobs.get(jid)
        if job is not None:
            job["status"] = JobStatus.FAILED
        self.job_finished.emit(jid, JobResult(success=False, error=err))

    def _on_thread_finished(self) -> None:
        thread = self.sender()
        _ACTIVE.pop(thread, None)
        for jid, job in list(self._jobs.items()):
            if job.get("thread") is thread:
                job["thread"] = None
                job["worker"] = None
                break
