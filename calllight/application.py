"""
Main application object.
"""

from __future__ import annotations

import socket
import time

from .config import Config
from .config import load_config
from .logger import configure_logger
from .version import __version__


class CallLight:
    """
    Main application.

    All runtime state is stored inside this object.
    """

    def __init__(self) -> None:

        self.start_time = time.monotonic()

        self.config: Config = load_config()

        self.logger = configure_logger(self.config.debug)

        self.hostname = socket.gethostname()

        #
        # Runtime state
        #

        self.running = True

        self.state = "IDLE"

        self.peers: dict[str, dict] = {}

        self.events: list[dict] = []

        self.logger.info("Starting Call Light")

        self.logger.info("Version: %s", __version__)

        self.logger.info("Hostname: %s", self.hostname)

    @property
    def uptime(self) -> int:
        """
        Application uptime in seconds.
        """

        return int(time.monotonic() - self.start_time)

    def peer_count(self) -> int:
        """
        Number of currently discovered peers.
        """

        return len(self.peers)

    def add_event(self, event: str) -> None:
        """
        Add an event to the in-memory log.
        """

        self.events.append(
            {
                "timestamp": time.time(),
                "message": event,
            }
        )

        #
        # Keep only the most recent 200 events.
        #

        self.events = self.events[-200:]

        self.logger.info(event)

    def status(self) -> dict:
        """
        Current application status.

        Used by the Web UI and API.
        """

        return {

            "version": __version__,
            "hostname": self.hostname,
            "state": self.state,
            "uptime": self.uptime,
            "peer_count": self.peer_count(),
            "running": self.running,

        }

    def run(self) -> None:
        """
        Placeholder application loop.

        The Flask server, networking and GPIO tasks
        will be started here in future commits.
        """

        self.logger.info("Application initialised.")

        self.logger.info("Waiting for Web UI startup...")
