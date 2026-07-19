"""
Application constants.

All fixed values used throughout the application should live here.
"""

from pathlib import Path

APP_NAME = "Call Light"
LOG_NAME = "call-light"

VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"

DEFAULT_HTTP_PORT = 8080

DEFAULT_BUTTON_GPIO = 17
DEFAULT_LED_GPIO = 27

DEFAULT_FLASH_RATE_MS = 250

DEFAULT_LOG_LEVEL = "INFO"

LOG_DIRECTORY = Path("/var/log/call-light")

WEB_TITLE = "Call Light"
