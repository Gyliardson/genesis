"""Minimal smoke test for the research scaffold."""

from genesis import __version__


def test_package_imports() -> None:
    assert __version__ == "0.0.0"
