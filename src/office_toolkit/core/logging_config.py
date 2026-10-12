import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .config import AppConfig


def _redact_path(path: str) -> str:
    """Redact sensitive paths; return shortened form."""
    return Path(path).as_posix()[-200:] if len(path) > 200 else path


def setup_logging(config: AppConfig, log_file: Optional[str] = None) -> logging.Logger:
    """Configure local logging (no network)."""
    logger = logging.getLogger("office_toolkit")
    logger.setLevel(config.log_level)
    logger.propagate = False

    if logger.handlers:
        return logger

    log_path = Path(log_file) if log_file else config.logs_dir / "office_toolkit.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_path,
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Also to stderr
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger.info("logging_initialized", extra={"log_path": str(log_path)})
    return logger
