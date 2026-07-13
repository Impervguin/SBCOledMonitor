# src/config.py

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import yaml


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
class LumaConfig:
    bus: int
    address: str


@dataclass(slots=True)
class ESPBridgeConfig:
    port: str
    sda: int
    scl: int
    ble: bool = False


@dataclass(slots=True)
class AppSettings:
    update_interval: int
    log_dir: str
    log_level: str = "INFO"


@dataclass(slots=True)
class AppConfig:
    display: DisplayConfig
    app: AppSettings
    luma: LumaConfig | None = None
    espbridge: ESPBridgeConfig | None = None


def load_config(path: str | Path) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    display = DisplayConfig(
        backend=BackendType(data["display"]["backend"]),
        width=data["display"]["width"],
        height=data["display"]["height"],
        rotate=data["display"].get("rotate", 0),
    )

    app = AppSettings(
        update_interval=data["app"]["update_interval"],
        log_dir=data["app"]["log_dir"],
        log_level=data["app"].get("log_level", "INFO"),
    )

    luma = None
    if "luma" in data:
        luma = LumaConfig(**data["luma"])

    espbridge = None
    if "espbridge" in data:
        espbridge = ESPBridgeConfig(**data["espbridge"])

    return AppConfig(
        display=display,
        app=app,
        luma=luma,
        espbridge=espbridge,
    )