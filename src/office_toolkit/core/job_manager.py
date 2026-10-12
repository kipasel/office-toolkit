from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional
import time

from PySide6.QtCore import QObject, QThread, Signal


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

    def __init__(self, func: Callable[[], JobResult], can_cancel: bool = False):
        super().__init__()
        self._func = func
        self._cancelled = False
        self._can_cancel = can_cancel

    def cancel(self) -> None:
        if self._can_cancel:
            self._cancelled = True

    def run(self) -> None:
        try:
            self.started.emit()
            # If can_cancel, func should check; but keep simple
            if self._can_cancel and self._cancelled:
                self.finished.emit(JobResult(success=False, error="Dibatalkan"))
                return
            res = self._func()
            if self._can_cancel and self._cancelled and res.success:
                res = JobResult(success=False, error="Dibatalkan")
            self.finished.emit(res)
        except Exception as e:
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
        worker = Worker(func, can_cancel=can_cancel)
        worker.moveToThread(thread)
        worker.progress.connect(lambda p: self.job_progress.emit(jid, p))
        worker.started.connect(lambda: self.job_started.emit(jid))
        worker.finished.connect(lambda res: self._on_finished(jid, thread, worker, res))
        worker.failed.connect(lambda err: self._on_failed(jid, thread, worker, err))
        thread.started.connect(worker.run)
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
        w: Worker = job["worker"]
        w.cancel()
        job["status"] = JobStatus.CANCELLED

    def _on_finished(self, jid: str, thread: QThread, worker: Worker, res: JobResult) -> None:
        job = self._jobs.get(jid)
        if job:
            job["status"] = JobStatus.SUCCEEDED if res.success else JobStatus.FAILED
        self.job_finished.emit(jid, res)
        thread.quit()
        thread.wait()
        worker.deleteLater()
        thread.deleteLater()

    def _on_failed(self, jid: str, thread: QThread, worker: Worker, err: str) -> None:
        job = self._jobs.get(jid)
        if job:
            job["status"] = JobStatus.FAILED
        res = JobResult(success=False, error=err)
        self.job_finished.emit(jid, res)
        thread.quit()
        thread.wait()
        worker.deleteLater()
        thread.deleteLater()
