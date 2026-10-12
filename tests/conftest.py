"""Shared pytest fixtures and sys.path setup for the test suite."""

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_TESTS = Path(__file__).resolve().parent
_SRC = _ROOT / "src"

for _p in (str(_SRC), str(_TESTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fixtures.pdf_factory import make_corrupt_pdf, make_encrypted_pdf, make_pdf  # noqa: E402


@pytest.fixture
def pdf_factory():
    """Return the synthetic PDF factory helpers."""
    import fixtures.pdf_factory as factory

    return factory


@pytest.fixture
def sample_pdf(tmp_path):
    """A 5-page PDF with labeled pages P1..P5."""
    return make_pdf(tmp_path / "sample.pdf", [f"P{i}" for i in range(1, 6)])


@pytest.fixture
def encrypted_pdf(tmp_path):
    return make_encrypted_pdf(tmp_path / "encrypted.pdf", user_pw="rahasia")


@pytest.fixture
def corrupt_pdf(tmp_path):
    return make_corrupt_pdf(tmp_path / "corrupt.pdf")
