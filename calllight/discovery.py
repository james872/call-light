"""
mDNS peer discovery.

Each station registers a service and browses for others. Discovery
only ever ADDS peers and their addresses - it never determines
liveness. A vanished mDNS record means nothing; only missed
heartbeats mark a peer offline.
"""

from __future__ import annotations

import socket
import threading

from zeroconf import ServiceBrowser
from zeroconf import ServiceInfo
from zeroconf import Zeroconf

from .constants import MDNS_SERVICE_TYPE
from .constants import PROTOCOL_VERSION


def _local_ip() -> str:
    """
    Best-effort local IP address.

    Opens a UDP socket towards a routable address; no packet is
    actually sent.
    """

    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:

        probe.connect(("10.255.255.255", 1))

        return probe.getsockname()[0]

    except OSError:

        return "127.0.0.1"

    finally:

        probe.close()


class Discovery:
    """
    mDNS registration and browsing for one station.
    """

    def __init__(self, calllight, messaging) -> None:

        self.app = calllight
        self.messaging = messaging

        self.zeroconf: Zeroconf | None = None
        self.info: ServiceInfo | None = None
        self.browser: ServiceBrowser | None = None
        self.lock = threading.RLock()

    def start(self) -> None:
        """
        Register this station and start browsing for peers.
        """

        address = _local_ip()

        info = ServiceInfo(

            MDNS_SERVICE_TYPE,

            "%s.%s" % (self.app.station_id, MDNS_SERVICE_TYPE),

            addresses=[socket.inet_aton(address)],

            port=self.app.config.messaging_port,

            properties={
                "station_id": self.app.station_id,
                "display_name": self.app.display_name,
                "protocol": str(PROTOCOL_VERSION),
                "http_port": str(self.app.config.http_port),
            },

        )

        with self.lock:

            if self.zeroconf is not None:
                return

            self.zeroconf = Zeroconf()
            self.zeroconf.register_service(info)
            self.info = info
            self.browser = ServiceBrowser(self.zeroconf, MDNS_SERVICE_TYPE, self)

        self.app.logger.info(
            "Discovery started (%s on %s)", self.app.station_id, address
        )

    def restart(self) -> None:
        """Re-register mDNS after Wi-Fi obtains a new network interface."""
        self.stop()
        self.start()

    def stop(self) -> None:
        """Release mDNS resources before recreating them on a new interface."""
        with self.lock:
            if self.browser is not None:
                self.browser.cancel()
                self.browser = None
            if self.zeroconf is not None and self.info is not None:
                try:
                    self.zeroconf.unregister_service(self.info)
                except Exception:
                    pass
            if self.zeroconf is not None:
                self.zeroconf.close()
            self.info = None
            self.zeroconf = None

    #
    # ServiceBrowser listener interface
    #

    def add_service(self, zeroconf, service_type, name) -> None:

        info = zeroconf.get_service_info(service_type, name)

        if info is None:
            return

        properties = {
            key.decode(): value.decode()
            for key, value in info.properties.items()
            if value is not None
        }

        station_id = properties.get("station_id")

        if station_id is None or station_id == self.app.station_id:
            return

        address = socket.inet_ntoa(info.addresses[0])

        self.app.record_peer(
            station_id,
            display_name=properties.get("display_name", station_id[:8]),
            address=address,
            messaging_port=info.port,
        )

        self.messaging.connect_peer(address, info.port)

    def update_service(self, zeroconf, service_type, name) -> None:

        self.add_service(zeroconf, service_type, name)

    def remove_service(self, zeroconf, service_type, name) -> None:

        #
        # Deliberately nothing: discovery never marks peers
        # offline. Heartbeat timeout does.
        #

        pass
