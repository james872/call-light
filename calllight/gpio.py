"""
GPIO button and LED.

The button routes through the same press handler as the web UI.

The LED strictly mirrors the call state: flashing while Calling,
off while Idle. It deliberately shows nothing else - no liveness,
no errors.
"""

from __future__ import annotations

import threading
import time

from .constants import STATE_CALLING


class Gpio:
    """
    GPIO handling for one station.
    """

    def __init__(self, calllight) -> None:

        self.app = calllight

        self.button = None
        self.led = None
        self.error = None
        self.led_on = False
        self.setup_window_seconds = 60
        self.setup_hold_seconds = 10

    def start(self) -> None:
        """
        Attach the button and start the LED flasher.

        On machines without GPIO (development), this logs a warning
        and does nothing - the virtual button still works.
        """

        try:

            from gpiozero import Button, PWMLED

            self.button = Button(
                self.app.config.button_gpio,
                bounce_time=0.05,
            )

            #
            # PWM so the brightness setting is a duty cycle.
            #

            self.led = PWMLED(self.app.config.led_gpio)

        except Exception as error:

            self.error = str(error)

            self.app.logger.warning(
                "GPIO unavailable (%s) - running without button/LED",
                error,
            )

            return

        self.button.when_pressed = lambda: self.app.press("button")

        threading.Thread(
            target=self._watch_for_setup_mode,
            name="setup-mode-watchdog",
            daemon=True,
        ).start()

        threading.Thread(
            target=self._flash_loop,
            name="led-flasher",
            daemon=True,
        ).start()

        self.app.logger.info(
            "GPIO started (button %d, LED %d)",
            self.app.config.button_gpio,
            self.app.config.led_gpio,
        )

    def snapshot(self) -> dict:
        """GPIO state suitable for display in the Web UI."""
        button_pressed = None
        if self.button is not None:
            try:
                button_pressed = self.button.is_pressed
            except Exception as error:
                self.error = str(error)

        return {
            "available": self.button is not None and self.led is not None,
            "button_gpio": self.app.config.button_gpio,
            "led_gpio": self.app.config.led_gpio,
            "button_pressed": button_pressed,
            "led_on": self.led_on,
            "backend": (
                None if self.button is None
                else type(self.button.pin_factory).__name__
            ),
            "error": self.error,
        }

    def _watch_for_setup_mode(self) -> None:
        """Accept a deliberate ten-second button hold only just after boot."""
        deadline = time.monotonic() + self.setup_window_seconds
        held_since = None

        while time.monotonic() < deadline and not self.app.setup_mode:
            try:
                pressed = self.button.is_pressed
            except Exception as error:
                self.error = str(error)
                return

            if pressed:
                held_since = held_since or time.monotonic()
                if time.monotonic() - held_since >= self.setup_hold_seconds:
                    self.app.enter_setup_mode()
                    return
            else:
                held_since = None

            time.sleep(0.05)

    def _flash_loop(self) -> None:

        while self.app.running:

            if self.app.setup_mode:
                self._setup_flash_pattern()
                continue

            #
            # Settings are read every cycle so changes from the
            # web UI apply immediately.
            #

            interval = self.app.config.flash_rate_ms / 1000.0

            brightness = self.app.config.led_brightness / 100.0

            if self.app.state == STATE_CALLING:

                self.led.value = brightness
                self.led_on = True
                time.sleep(interval)

                self.led.off()
                self.led_on = False
                time.sleep(interval)

            else:

                self.led.off()
                self.led_on = False
                time.sleep(0.05)

    def _setup_flash_pattern(self) -> None:
        """Three short flashes, then a three-second pause for setup mode."""
        for _ in range(3):
            self.led.value = self.app.config.led_brightness / 100.0
            self.led_on = True
            time.sleep(0.15)
            self.led.off()
            self.led_on = False
            time.sleep(0.15)
        time.sleep(3)
