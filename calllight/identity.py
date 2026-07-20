"""
Station identity.

The protocol identifies stations only by Station ID: a UUID
generated on first run and persisted locally. Hostname plays
no protocol role.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from .constants import STATION_ID_FILE


def get_station_id(path: Path = STATION_ID_FILE) -> str:
    """
    Load the persisted Station ID, generating it on first run.

    If the identity file cannot be written (development machine,
    read-only filesystem), an ephemeral ID is used for this run
    and a warning is logged.

    Returns
    -------
    str
        The Station ID.
    """

    logger = logging.getLogger("call-light")

    if path.exists():

        station_id = path.read_text().strip()

        if station_id:
            return station_id

    station_id = str(uuid.uuid4())

    try:

        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(station_id + "\n")

        logger.info("Generated new Station ID: %s", station_id)

    except OSError:

        logger.warning(
            "Could not persist Station ID to %s - using ephemeral ID %s",
            path,
            station_id,
        )

    return station_id
