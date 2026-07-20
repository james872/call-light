"""
Configuration handling.

Loads configuration from:

/etc/call-light/config.yaml

The path can be overridden with the CALL_LIGHT_CONFIG environment
variable, which allows several stations to run on one machine
during development.

If the file does not exist, sensible defaults are used.
"""

from dataclasses import dataclass
from pathlib import Path
import os
import socket

import yaml

from .constants import DEFAULT_BUTTON_GPIO
from .constants import DEFAULT_FLASH_RATE_MS
from .constants import DEFAULT_HTTP_PORT
from .constants import DEFAULT_LED_BRIGHTNESS
from .constants import DEFAULT_LED_GPIO
from .constants import DEFAULT_MESSAGING_PORT
from .constants import STATION_ID_FILE


CONFIG_FILE = Path(
    os.environ.get("CALL_LIGHT_CONFIG", "/etc/call-light/config.yaml")
)


@dataclass(slots=True)
class Config:

    hostname: str
    display_name: str

    button_gpio: int
    led_gpio: int

    http_port: int
    messaging_port: int

    flash_rate_ms: int
    led_brightness: int

    station_id_file: str

    debug: bool


def load_config() -> Config:
    """
    Load configuration.

    Returns
    -------
    Config
    """

    #
    # Hostname is informational only.
    # It is never used as a station identity - see identity.py.
    #

    hostname = socket.gethostname()

    defaults = {

        "hostname": hostname,
        "display_name": hostname,

        "button_gpio": DEFAULT_BUTTON_GPIO,
        "led_gpio": DEFAULT_LED_GPIO,

        "http_port": DEFAULT_HTTP_PORT,
        "messaging_port": DEFAULT_MESSAGING_PORT,

        "flash_rate_ms": DEFAULT_FLASH_RATE_MS,
        "led_brightness": DEFAULT_LED_BRIGHTNESS,

        "station_id_file": str(STATION_ID_FILE),

        "debug": True,

    }

    if CONFIG_FILE.exists():

        with CONFIG_FILE.open("r") as f:

            loaded = yaml.safe_load(f) or {}

            defaults.update(loaded)

    return Config(**defaults)


def save_config(config: Config) -> None:
    """
    Persist the current configuration.

    Hostname is deliberately not written: it is runtime-derived,
    and freezing it in the file would shadow later renames.
    """

    settings = {

        "display_name": config.display_name,

        "button_gpio": config.button_gpio,
        "led_gpio": config.led_gpio,

        "http_port": config.http_port,
        "messaging_port": config.messaging_port,

        "flash_rate_ms": config.flash_rate_ms,
        "led_brightness": config.led_brightness,

        "station_id_file": config.station_id_file,

        "debug": config.debug,

    }

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with CONFIG_FILE.open("w") as f:

        yaml.safe_dump(settings, f, default_flow_style=False)
