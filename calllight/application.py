"""
Main application object.
"""

from __future__ import annotations

import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from .config import Config
from .config import load_config
from .config import save_config
from .constants import DISPLAY_NAME_MAX_LENGTH
from .constants import EVENT_CALL
from .constants import EVENT_CLEAR
from .constants import FLASH_RATE_MAX_MS
from .constants import FLASH_RATE_MIN_MS
from .constants import LED_BRIGHTNESS_MAX
from .constants import LED_BRIGHTNESS_MIN
from .constants import MAX_EVENTS
from .constants import PEER_TIMEOUT_S
from .constants import PROTOCOL_VERSION
from .constants import STATE_CALLING
from .constants import STATE_IDLE
from .identity import get_station_id
from .logger import configure_logger
from .version import __version__


class CallLight:
    """
    Main application.

    All runtime state is stored inside this object.

    The call state is versioned: every transition carries a
    (counter, origin station id) pair. A station adopts any state
    with a newer version, which is what lets heartbeats repair
    missed events. See ADR 0001.
    """

    def __init__(self) -> None:

        self.start_time = time.monotonic()

        self.config: Config = load_config()

        self.logger = configure_logger(self.config.debug)

        self.hostname = socket.gethostname()

        self.station_id = get_station_id(Path(self.config.station_id_file))

        self.display_name = self.config.display_name

        #
        # Runtime state
        #

        self.running = True

        self.state = STATE_IDLE

        self.state_counter = 0
        self.state_origin = self.station_id

        self.lock = threading.RLock()

        #
        # Peers, keyed by Station ID.
        #
        # Each entry holds: display_name, address, messaging_port,
        # http_port, last_seen (monotonic), protocol_version, state.
        #

        self.peers: dict[str, dict] = {}

        self.events: list[dict] = []

        #
        # Set by the messaging layer once it is started.
        # Called with (event_type) to broadcast a local press.
        #

        self.transport = None
        self.gpio = None
        self.network = None
        self.setup_mode = False
        self.setup_ssid = None

        self.logger.info("Starting Call Light")

        self.logger.info("Version: %s", __version__)

        self.logger.info("Station ID: %s", self.station_id)

        self.logger.info("Display name: %s", self.display_name)

    @property
    def uptime(self) -> int:
        """
        Application uptime in seconds.
        """

        return int(time.monotonic() - self.start_time)

    #
    # State versioning
    #

    def _is_newer(self, counter: int, origin: str) -> bool:
        """
        Whether (counter, origin) is newer than our current version.

        Higher counter wins; on a tie the higher origin id wins,
        which is arbitrary but deterministic on every station.
        """

        if counter != self.state_counter:
            return counter > self.state_counter

        return origin > self.state_origin

    def press(self, source: str) -> str:
        """
        Handle a Press from any source (GPIO button or web UI).

        The toggle is interpreted locally: a Press while Idle
        becomes a CALL, a Press while Calling becomes a CLEAR.

        Returns
        -------
        str
            The event type that was generated.
        """

        with self.lock:

            if self.state == STATE_IDLE:

                event_type = EVENT_CALL
                self.state = STATE_CALLING

            else:

                event_type = EVENT_CLEAR
                self.state = STATE_IDLE

            self.state_counter += 1
            self.state_origin = self.station_id

            self.add_event(event_type, self.station_id, self.display_name)

        if self.transport is not None:
            self.transport.broadcast_event(event_type)

        self.logger.info("Local press (%s) -> %s", source, event_type)

        return event_type

    def apply_event(
        self,
        event_type: str,
        counter: int,
        origin: str,
        origin_name: str,
    ) -> None:
        """
        Apply a CALL or CLEAR event received from a peer.

        The event is always logged - it happened - but the state
        is only adopted if the version is newer than ours.
        """

        with self.lock:

            self.add_event(event_type, origin, origin_name)

            if not self._is_newer(counter, origin):
                return

            self.state_counter = counter
            self.state_origin = origin

            if event_type == EVENT_CALL:
                self.state = STATE_CALLING
            else:
                self.state = STATE_IDLE

    def apply_heartbeat_state(
        self,
        state: str,
        counter: int,
        origin: str,
        from_id: str,
        from_name: str,
    ) -> None:
        """
        Reconcile against the (state, version) carried by a heartbeat.

        This is the repair path for missed events and mid-call boots.
        Adopting a state change from a heartbeat is logged so the
        Event Log never silently diverges from the light.
        """

        with self.lock:

            if not self._is_newer(counter, origin):
                return

            if state == self.state:

                #
                # Same state, newer version - adopt silently.
                #

                self.state_counter = counter
                self.state_origin = origin

                return

            self.state = state
            self.state_counter = counter
            self.state_origin = origin

            event_type = (
                EVENT_CALL if state == STATE_CALLING else EVENT_CLEAR
            )

            self.add_event(
                event_type,
                origin,
                self.peer_display_name(origin),
                note="via heartbeat from %s" % from_name,
            )

            self.logger.info(
                "Adopted %s (version %s) from heartbeat", state, counter
            )

    #
    # Peers
    #

    def record_peer(self, station_id: str, **fields) -> None:
        """
        Create or update a peer entry.

        Called by discovery (address, ports, display name) and by
        the messaging layer on every received message (last_seen,
        protocol_version, state).
        """

        if station_id == self.station_id:
            return

        with self.lock:

            peer = self.peers.setdefault(station_id, {

                "display_name": station_id[:8],
                "address": None,
                "messaging_port": None,
                "last_seen": None,
                "protocol_version": None,
                "state": None,

            })

            peer.update(fields)

    def peer_display_name(self, station_id: str) -> str:
        """
        Best known display name for a station id.
        """

        if station_id == self.station_id:
            return self.display_name

        peer = self.peers.get(station_id)

        if peer is None:
            return station_id[:8]

        return peer["display_name"]

    def peer_status(self, peer: dict) -> str:
        """
        Derived status of a peer entry.

        Discovery never determines liveness - only heartbeats do.
        """

        if (
            peer["protocol_version"] is not None
            and peer["protocol_version"] != PROTOCOL_VERSION
        ):
            return "incompatible"

        if peer["last_seen"] is None:
            return "offline"

        if time.monotonic() - peer["last_seen"] > PEER_TIMEOUT_S:
            return "offline"

        return "online"

    def peer_snapshot(self) -> list[dict]:
        """
        Peer list for the Web UI and API.
        """

        with self.lock:

            snapshot = []

            for station_id, peer in sorted(
                self.peers.items(),
                key=lambda item: item[1]["display_name"],
            ):

                last_seen = peer["last_seen"]

                snapshot.append({

                    "station_id": station_id,
                    "display_name": peer["display_name"],
                    "address": peer["address"],
                    "status": self.peer_status(peer),
                    "last_seen_seconds": (
                        None
                        if last_seen is None
                        else round(time.monotonic() - last_seen)
                    ),
                    "protocol_version": peer["protocol_version"],

                })

            return snapshot

    def online_peer_count(self) -> int:
        """
        Number of peers currently online.
        """

        with self.lock:

            return sum(
                1
                for peer in self.peers.values()
                if self.peer_status(peer) == "online"
            )

    #
    # Settings
    #

    def settings(self) -> dict:
        """
        Per-station settings for the Web UI.
        """

        with self.lock:

            status = {

                "display_name": self.display_name,
                "flash_rate_ms": self.config.flash_rate_ms,
                "led_brightness": self.config.led_brightness,

            }

    def update_settings(
        self,
        display_name: str | None = None,
        flash_rate_ms: int | None = None,
        led_brightness: int | None = None,
    ) -> dict:
        """
        Apply and persist per-station settings.

        A Display Name change propagates to peers automatically on
        the next heartbeat, and also renames the machine (sanitized)
        so the network address matches the label.

        Returns
        -------
        dict
            The settings that actually changed.
        """

        changed: dict = {}

        with self.lock:

            if display_name is not None:

                display_name = str(display_name).strip()
                display_name = display_name[:DISPLAY_NAME_MAX_LENGTH]

                if display_name and display_name != self.display_name:

                    self.display_name = display_name
                    self.config.display_name = display_name

                    changed["display_name"] = display_name

            if flash_rate_ms is not None:

                flash_rate_ms = max(
                    FLASH_RATE_MIN_MS,
                    min(FLASH_RATE_MAX_MS, int(flash_rate_ms)),
                )

                if flash_rate_ms != self.config.flash_rate_ms:

                    self.config.flash_rate_ms = flash_rate_ms

                    changed["flash_rate_ms"] = flash_rate_ms

            if led_brightness is not None:

                led_brightness = max(
                    LED_BRIGHTNESS_MIN,
                    min(LED_BRIGHTNESS_MAX, int(led_brightness)),
                )

                if led_brightness != self.config.led_brightness:

                    self.config.led_brightness = led_brightness

                    changed["led_brightness"] = led_brightness

        if changed:

            try:

                save_config(self.config)

            except OSError as error:

                self.logger.warning(
                    "Could not persist settings: %s", error
                )

            self.logger.info("Settings changed: %s", changed)

        if "display_name" in changed:

            self._sync_hostname(changed["display_name"])

        return changed

    def _sync_hostname(self, display_name: str) -> None:
        """
        Rename the machine to match the Display Name.

        Best effort: on machines where this fails (development
        boxes, restricted containers) the rename is logged and
        skipped - the Display Name itself is unaffected.
        """

        slug = re.sub(r"[^a-z0-9]+", "-", display_name.lower()).strip("-")

        if not slug:
            return

        hostname = "call-%s" % slug

        if hostname == self.hostname:
            return

        if sys.platform == "win32":

            self.logger.info(
                "Skipping hostname change on this platform"
            )

            return

        try:

            subprocess.run(
                ["hostnamectl", "set-hostname", hostname],
                capture_output=True,
                timeout=10,
                check=True,
            )

        except (subprocess.SubprocessError, OSError):

            #
            # No hostnamectl (or no dbus). Fall back to the
            # classic mechanism.
            #

            try:

                Path("/etc/hostname").write_text(hostname + "\n")

                subprocess.run(
                    ["hostname", hostname],
                    capture_output=True,
                    timeout=10,
                    check=True,
                )

            except (subprocess.SubprocessError, OSError) as error:

                self.logger.warning(
                    "Could not change hostname: %s", error
                )

                return

        #
        # Keep /etc/hosts resolving the new name.
        #

        try:

            hosts = Path("/etc/hosts")

            content = hosts.read_text()

            if self.hostname and self.hostname in content:

                hosts.write_text(
                    content.replace(self.hostname, hostname)
                )

        except OSError:

            pass

        self.logger.info(
            "Hostname changed: %s -> %s", self.hostname, hostname
        )

        self.hostname = hostname

    #
    # Events
    #

    def add_event(
        self,
        event_type: str,
        origin_id: str,
        origin_name: str,
        note: str | None = None,
    ) -> None:
        """
        Add a Call or Clear event to the in-memory Event Log.

        The log is this station's local view. Timestamps are
        best-effort wall-clock time.
        """

        with self.lock:

            self.events.append(
                {
                    "timestamp": time.time(),
                    "type": event_type,
                    "origin_id": origin_id,
                    "origin_name": origin_name,
                    "note": note,
                }
            )

            #
            # Keep only the most recent events.
            #

            self.events = self.events[-MAX_EVENTS:]

        self.logger.info(
            "Event: %s from %s%s",
            event_type,
            origin_name,
            " (%s)" % note if note else "",
        )

    def event_snapshot(self) -> list[dict]:
        """
        Event Log for the Web UI and API, newest first.
        """

        with self.lock:

            return list(reversed(self.events))

    def enter_setup_mode(self) -> str:
        """Start the temporary local Wi-Fi setup network once per boot."""
        with self.lock:
            if self.setup_mode:
                return self.setup_ssid or ""
            if self.network is None:
                raise RuntimeError("Network manager is unavailable")
            ssid = self.network.setup_ssid()
            self.setup_mode = True
            self.setup_ssid = ssid

        self.logger.info("Entering setup mode")

        def start_hotspot() -> None:
            try:
                self.setup_ssid = self.network.start_setup_hotspot()
                self.logger.info(
                    "Setup hotspot %s started at http://192.168.2.1:8080",
                    self.setup_ssid,
                )
            except (OSError, RuntimeError, subprocess.SubprocessError) as error:
                self.logger.warning("Could not start setup hotspot: %s", error)

        threading.Thread(target=start_hotspot, name="setup-hotspot", daemon=True).start()
        return ssid

    def exit_setup_mode(self) -> None:
        """Leave setup mode, restore normal Wi-Fi behaviour, and restart."""
        with self.lock:
            if not self.setup_mode:
                return
            self.setup_mode = False

        self.logger.info("Leaving setup mode and restarting service")

        def stop_hotspot_and_restart() -> None:
            try:
                if self.network is not None:
                    self.network.stop_setup_hotspot()
            except (OSError, RuntimeError, subprocess.SubprocessError) as error:
                self.logger.warning("Could not stop setup hotspot: %s", error)
            subprocess.Popen(["systemctl", "restart", "call-light.service"])

        threading.Thread(
            target=stop_hotspot_and_restart,
            name="setup-mode-exit",
            daemon=True,
        ).start()

    #
    # Status
    #

    def status(self) -> dict:
        """
        Current application status.

        Used by the Web UI and API.
        """

        with self.lock:

            status = {

                "version": __version__,
                "protocol_version": PROTOCOL_VERSION,
                "station_id": self.station_id,
                "display_name": self.display_name,
                "hostname": self.hostname,
                "state": self.state,
                "state_counter": self.state_counter,
                "uptime": self.uptime,
                "peer_count": len(self.peers),
                "online_peer_count": self.online_peer_count(),
                "running": self.running,
                "setup_mode": self.setup_mode,
                "setup_ssid": self.setup_ssid,

            }

        if self.gpio is not None:
            status["gpio"] = self.gpio.snapshot()

        return status
