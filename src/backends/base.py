from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from PIL import ImageDraw


class DisplayBackend(ABC):
    @property
    @abstractmethod
    def width(self) -> int:
        ...

    @property
    @abstractmethod
    def height(self) -> int:
        ...

    @abstractmethod
    def initialize(self) -> None:
        ...

    @abstractmethod
    def clear(self) -> None:
        ...

    @abstractmethod
    def draw(self) -> AbstractContextManager[ImageDraw.ImageDraw]:
        ...

    def close(self) -> None:
        """Optional cleanup."""
        pass

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()