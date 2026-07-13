from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

from src.config import AppConfig
from .base import DisplayBackend


class LumaBackend(DisplayBackend):
    def __init__(self, config: AppConfig):
        if config.luma is None:
            raise ValueError("Luma backend requires luma configuration")

        self._cfg = config
        self._device = None

    @property
    def width(self) -> int:
        return self._cfg.display.width

    @property
    def height(self) -> int:
        return self._cfg.display.height

    def initialize(self) -> None:
        serial = i2c(
            port=self._cfg.luma.bus,
            address=self._cfg.luma.address,
        )

        self._device = ssd1306(
            serial,
            width=self.width,
            height=self.height,
            rotate=self._cfg.display.rotate,
        )

        self._device.clear()

    def draw(self):
        return canvas(self._device)

    def clear(self) -> None:
        self._device.clear()