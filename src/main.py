#!/usr/bin/env python3

import logging
import os
import sys

from src.config import load_config
from src.monitor import OLEDMonitor


def main():

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config = load_config(
        os.getenv(
            "CONFIG_PATH",
            "/etc/oled-monitor/config.yaml",
        )
    )

    try:
        OLEDMonitor(config).run()

    except KeyboardInterrupt:
        pass

    except Exception:
        logging.exception("OLED monitor crashed")
        sys.exit(1)


if __name__ == "__main__":
    main()