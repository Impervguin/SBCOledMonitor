from espbridge import Bridge
from espbridge.drivers.oled import OLED

from src.config import AppConfig
from .base import DisplayBackend


class ESPBridgeBackend(DisplayBackend):
    def __init__(self, config: AppConfig):
        if config.espbridge is None:
            raise ValueError("ESPBridge backend requires espbridge configuration")

        self._cfg = config

        self._bridge = None
        self._oled = None

    @property
    def width(self) -> int:
        return self._cfg.display.width

    @property
    def height(self) -> int:
        return self._cfg.display.height

    def initialize(self) -> None:
        cfg = self._cfg.espbridge

        self._bridge = Bridge(
            ble=cfg.ble,
            port=cfg.port,
        )

        self._bridge.__enter__()

        self._bridge.i2c.init(
            sda=cfg.sda,
            scl=cfg.scl,
        )

        self._oled = OLED(
            self._bridge,
            width=self._cfg.display.width,
            height=self._cfg.display.height,)

    def draw(self):
        return self._oled.draw()

    def clear(self) -> None:
        # Библиотека очищает экран при пустом draw().
        with self._oled.draw():
            pass

    def close(self) -> None:
        if self._bridge is not None:
            self._bridge.__exit__(None, None, None)
            self._bridge = None