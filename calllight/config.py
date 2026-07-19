"""
Configuration handling.

Loads configuration from:

/etc/call-light/config.yaml

If the file does not exist, sensible defaults are used.
"""

from dataclasses import dataclass
from pathlib import Path
import socket

import yaml


CONFIG_FILE = Path("/etc/call-light/config.yaml")


@dataclass(slots=True)
class Config:

    hostname: str
    display_name: str

    button_gpio: int
    led_gpio: int

    http_port: int

    flash_rate_ms: int

    debug: bool


def load_config() -> Config:
    """
    Load configuration.

    Returns
    -------
    Config
    """

    hostname = socket.gethostname()

    defaults = {

        "hostname": hostname,
        "display_name": hostname,

        "button_gpio": 17,
        "led_gpio": 27,

        "http_port": 8080,

        "flash_rate_ms": 250,

        "debug": True,

    }

    if CONFIG_FILE.exists():

        with CONFIG_FILE.open("r") as f:

            loaded = yaml.safe_load(f) or {}

            defaults.update(loaded)

    return Config(**defaults)
