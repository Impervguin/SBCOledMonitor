from src.config import AppConfig, BackendType

from .base import DisplayBackend
from .espbridge import ESPBridgeBackend
from .luma import LumaBackend


_BACKENDS: dict[BackendType, type[DisplayBackend]] = {
    BackendType.luma: LumaBackend,
    BackendType.espbridge: ESPBridgeBackend,
}


def create_backend(config: AppConfig) -> DisplayBackend:
    try:
        backend_cls = _BACKENDS[config.display.backend]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported backend: {config.display.backend}"
        ) from exc

    return backend_cls(config)