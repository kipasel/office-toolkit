import tomllib
from pathlib import Path

from office_toolkit import __version__


def test_version_matches_pyproject():
    """``__version__`` must stay in sync with the packaged project version."""
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with pyproject.open("rb") as fh:
        declared = tomllib.load(fh)["project"]["version"]
    assert __version__ == declared
