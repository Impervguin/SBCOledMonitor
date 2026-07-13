# src/backends/luma.py

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

from .base import DisplayBackend


class LumaBackend(DisplayBackend):

    def __init__(self, config: dict):
        self._config = config
        self._device = None

    @property
    def width(self):
        return self._config["display"]["width"]

    @property
    def height(self):
        return self._config["display"]["height"]

    def initialize(self):

        serial = i2c(
            port=self._config["i2c"]["bus"],
            address=int(self._config["i2c"]["address"]),
        )

        self._device = ssd1306(
            serial,
            width=self.width,
            height=self.height,
            rotate=self._config["display"]["rotate"],
        )

        self._device.clear()

    def clear(self):
        self._device.clear()

    def canvas(self):
        return canvas(self._device)