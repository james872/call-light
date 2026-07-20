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

            self.app.logger.warning(
                "GPIO unavailable (%s) - running without button/LED",
                error,
            )

            return

        self.button.when_pressed = lambda: self.app.press("button")

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

    def _flash_loop(self) -> None:

        while self.app.running:

            #
            # Settings are read every cycle so changes from the
            # web UI apply immediately.
            #

            interval = self.app.config.flash_rate_ms / 1000.0

            brightness = self.app.config.led_brightness / 100.0

            if self.app.state == STATE_CALLING:

                self.led.value = brightness
                time.sleep(interval)

                self.led.off()
                time.sleep(interval)

            else:

                self.led.off()
                time.sleep(0.05)
