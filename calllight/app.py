"""
Application entry point.
"""

from __future__ import annotations

from .application import CallLight
from .webui import create_web_app


def main() -> None:

    calllight = CallLight()

    web = create_web_app(calllight)

    calllight.logger.info(
        "Starting web server on port %s",
        calllight.config.http_port,
    )

    web.run(
        host="0.0.0.0",
        port=calllight.config.http_port,
        debug=False,
    )


if __name__ == "__main__":
    main()
