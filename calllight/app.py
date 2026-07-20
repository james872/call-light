"""
Application entry point.
"""

from __future__ import annotations

from .application import CallLight
from .discovery import Discovery
from .gpio import Gpio
from .messaging import Messaging
from .webui import create_web_app


def main() -> None:

    calllight = CallLight()

    messaging = Messaging(calllight)
    messaging.start()

    discovery = Discovery(calllight, messaging)
    discovery.start()

    gpio = Gpio(calllight)
    gpio.start()

    web = create_web_app(calllight)

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
