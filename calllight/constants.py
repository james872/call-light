"""
Application constants.

All fixed values used throughout the application should live here.
"""

from pathlib import Path

APP_NAME = "Call Light"
LOG_NAME = "call-light"

VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"

DEFAULT_HTTP_PORT = 8080
DEFAULT_MESSAGING_PORT = 5555

DEFAULT_BUTTON_GPIO = 17
DEFAULT_LED_GPIO = 27

DEFAULT_FLASH_RATE_MS = 250

#
# LED brightness in percent (PWM duty cycle while lit).
#

DEFAULT_LED_BRIGHTNESS = 100

FLASH_RATE_MIN_MS = 50
FLASH_RATE_MAX_MS = 2000

LED_BRIGHTNESS_MIN = 5
LED_BRIGHTNESS_MAX = 100

DISPLAY_NAME_MAX_LENGTH = 32

DEFAULT_LOG_LEVEL = "INFO"

LOG_DIRECTORY = Path("/var/log/call-light")

WEB_TITLE = "Call Light"

#
# Identity
#

STATION_ID_FILE = Path("/etc/call-light/station-id")

#
# Protocol
#
# The protocol version is independent of the application version.
# Bump it only when the wire format changes incompatibly.
# Peers speaking a different protocol version are ignored and
# shown in the web UI as incompatible.
#

PROTOCOL_VERSION = 1

MDNS_SERVICE_TYPE = "_call-light._tcp.local."

HEARTBEAT_INTERVAL_S = 2.0

#
# A peer missing three consecutive heartbeats is offline.
#

PEER_TIMEOUT_S = HEARTBEAT_INTERVAL_S * 3

#
# States
#

STATE_IDLE = "IDLE"
STATE_CALLING = "CALLING"

#
# Event types
#
# CALL and CLEAR are also wire message types, alongside HEARTBEAT.
#

EVENT_CALL = "CALL"
EVENT_CLEAR = "CLEAR"

MSG_HEARTBEAT = "HEARTBEAT"

MAX_EVENTS = 200
