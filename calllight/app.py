"""
Application entry point.
"""

from __future__ import annotations

import threading
import time

from .application import CallLight
from .discovery import Discovery
from .gpio import Gpio
from .messaging import Messaging
from .network import NetworkManager
from .webui import create_web_app


def main() -> None:

    calllight = CallLight()
    network = NetworkManager(calllight.logger)
    calllight.network = network

    messaging = Messaging(calllight)
    messaging.start()

    discovery = Discovery(calllight, messaging)
    discovery.start()

    def watch_connectivity() -> None:
        """Recreate mDNS discovery after a Wi-Fi disconnect/reconnect."""
        last_ip = None
        while calllight.running:
            current_ip = network.local_ip()
            if current_ip and current_ip != last_ip:
                if last_ip is not None:
                    calllight.logger.info(
                        "Wi-Fi address changed (%s -> %s); restarting discovery",
                        last_ip,
                        current_ip,
                    )
                else:
                    calllight.logger.info(
                        "Wi-Fi address available (%s); restarting discovery",
                        current_ip,
                    )
                discovery.restart()
            last_ip = current_ip
            time.sleep(2)

    threading.Thread(
        target=watch_connectivity,
        name="wifi-connectivity-watch",
        daemon=True,
    ).start()

    gpio = Gpio(calllight)
    calllight.gpio = gpio
    gpio.start()

    web = create_web_app(calllight, network)

    calllight.logger.info(
        "Starting web server on port %s",
        calllight.config.http_port,
    )

    web.run(
        host="0.0.0.0",
        port=calllight.config.http_port,
        debug=False,
        threaded=True,
    )


if __name__ == "__main__":
    main()
