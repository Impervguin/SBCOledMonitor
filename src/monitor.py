import logging
import signal
import time

from src.backends.factory import create_backend
from src.renderer import Renderer
from src.utils import (
    format_uptime,
    get_cpu_percent,
    get_cpu_temp,
    get_hostname,
    get_ram_usage,
    get_uptime,
)


class OLEDMonitor:
    def __init__(self, config):
        self.config = config
        self.running = True

        self.backend = create_backend(config)
        self.renderer = Renderer(self.backend)

        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def update(self):

        hostname = get_hostname()

        cpu_temp = get_cpu_temp()
        cpu_percent = get_cpu_percent()

        ram_usage, _, _ = get_ram_usage()

        uptime = format_uptime(get_uptime())

        self.renderer.render(
            hostname=hostname,
            uptime=uptime,
            cpu_percent=cpu_percent,
            cpu_temp=cpu_temp,
            ram_usage=ram_usage,
        )

    def run(self):

        interval = self.config.app.update_interval

        with self.backend:

            while self.running:
                self.update()
                time.sleep(interval)

    def _signal_handler(self, *_):
        self.running = False