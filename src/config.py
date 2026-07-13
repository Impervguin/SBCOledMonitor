from dataclasses import dataclass
from enum import StrEnum





class BackendType(StrEnum):
    luma = "luma"
    espbridge = "espbridge"


@dataclass(slots=True)
class DisplayConfig:
    backend: BackendType
    width: int
    height: int
    rotate: int = 0


@dataclass(slots=True)
class ESPBridgeConfig:
    port: str
    ble: bool = False

@dataclass(slots=True)
class LumaConfig:
    bus: int
    address: int


@dataclass(slots=True)
class AppConfig:
    display: DisplayConfig
    i2c: I2CConfig | None = None
    espbridge: ESPBridgeConfig | None = None