from pathlib import Path

from PIL import ImageFont

from src.backends.base import DisplayBackend
from src.utils import format_ram_usage


class Renderer:
    def __init__(self, backend: DisplayBackend):
        self.backend = backend

        self.font_large, self.font_medium, self.font_small = self._load_fonts()

    @staticmethod
    def _load_fonts():
        try:
            return (
                ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16
                ),
                ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10
                ),
                ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10
                ),
            )
        except Exception:
            font = ImageFont.load_default()
            return font, font, font

    @staticmethod
    def text_size(text: str, font):
        left, top, right, bottom = font.getbbox(text)
        return right - left, bottom - top

    def draw_centered(self, draw, text: str, y: int, font):
        w, _ = self.text_size(text, font)
        x = (self.backend.width - w) // 2
        draw.text((x, y), text, font=font, fill="white")

    def render(
        self,
        hostname: str,
        uptime: str,
        cpu_percent: float,
        cpu_temp: float,
        ram_usage: float,
    ):
        width = self.backend.width
        height = self.backend.height

        with self.backend.draw() as draw:

            draw.rectangle((0, 0, width, height), fill=0)

            hostname = hostname[:20]
            draw.text((0, 0), hostname, font=self.font_large, fill="white")

            uptime_text = f" {uptime}"
            uptime_width, _ = self.text_size(uptime_text, self.font_medium)

            draw.text(
                (width - uptime_width - 4, 0),
                uptime_text,
                font=self.font_medium,
                fill="white",
            )

            line = (
                f"{cpu_percent:2.1f}% | "
                f"{cpu_temp:>3.0f}°C | "
                f"{format_ram_usage(ram_usage, True)}"
            )

            self.draw_centered(draw, line, 22, self.font_small)