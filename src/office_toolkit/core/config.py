from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Application configuration with resource limits."""

    max_input_mb: int = 500
    max_image_pixels: int = 100_000_000
    max_pdf_pages_render: int = 5_000
    pdf_render_dpi_min: int = 36
    pdf_render_dpi_max: int = 600
    qr_decode_timeout_sec: int = 30
    max_csv_batch_rows: int = 100_000

    log_level: str = "INFO"

    app_dir: Path = field(default_factory=lambda: Path.home() / ".office_toolkit")
    logs_dir: Path = field(default_factory=lambda: Path.home() / ".office_toolkit" / "logs")
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".office_toolkit" / "cache")
    history_dir: Path = field(default_factory=lambda: Path.home() / ".office_toolkit" / "history")

    def ensure_dirs(self) -> None:
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)


_CONFIG: AppConfig | None = None


def get_config() -> AppConfig:
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = AppConfig()
        _CONFIG.ensure_dirs()
    return _CONFIG
