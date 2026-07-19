"""
Application version handling.
"""

from pathlib import Path


def _read_version() -> str:
    """
    Read the project VERSION file.

    Returns
    -------
    str
        Version string.
    """

    version_file = Path(__file__).resolve().parent.parent / "VERSION"

    try:
        return version_file.read_text().strip()

    except FileNotFoundError:
        return "Development"


__version__ = _read_version()
