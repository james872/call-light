"""
Update handling.

Install and update share one delivery mechanism: git clone plus
release tags. The updater fetches tags and checks out the newest
one - never the tip of main. Updates are strictly per-station.
See ADR 0002.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .version import __version__


REPO_ROOT = Path(__file__).resolve().parent.parent

UPDATE_SCRIPT = REPO_ROOT / "scripts" / "update.sh"


def _version_tuple(version: str) -> tuple[int, ...]:
    """
    Parse "v0.2.0" or "0.2.0" into a comparable tuple.
    """

    try:

        return tuple(
            int(part) for part in version.lstrip("v").split(".")
        )

    except ValueError:

        return (0,)


def _git(*args: str) -> str:

    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )

    return result.stdout.strip()


def check_for_update() -> dict:
    """
    Check GitHub for a newer release tag.

    Needs internet access; at a venue without it this simply
    reports the check failed, which is fine - updates are a
    between-gigs activity.
    """

    try:

        _git("fetch", "--tags", "--quiet")

        tags = _git("tag", "--sort=-v:refname").splitlines()

    except (subprocess.SubprocessError, OSError) as error:

        return {
            "current": __version__,
            "error": "Update check failed: %s" % error,
        }

    latest = tags[0] if tags else None

    available = (
        latest is not None
        and _version_tuple(latest) > _version_tuple(__version__)
    )

    return {
        "current": __version__,
        "latest": latest,
        "update_available": available,
    }


def start_update(logger) -> dict:
    """
    Launch the update script and return immediately.

    The script checks out the newest release tag, reinstalls
    dependencies and restarts the service, so this process will
    die mid-update. The script runs detached to survive that.
    """

    if not UPDATE_SCRIPT.exists():

        return {"error": "Update script not found: %s" % UPDATE_SCRIPT}

    if sys.platform == "win32":

        return {"error": "Updating is only supported on the station itself."}

    logger.info("Starting update via %s", UPDATE_SCRIPT)

    subprocess.Popen(
        ["/bin/bash", str(UPDATE_SCRIPT)],
        cwd=REPO_ROOT,
        start_new_session=True,
    )

    return {"status": "updating"}
