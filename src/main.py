#!/usr/bin/env python3
"""
OLED Monitor Service for Radxa Rock 4A
Displays system information on 0.91" OLED 128x32 display via I2C
"""

import sys
import os
import signal
import logging
import logging.handlers
import time
from pathlib import Path
from typing import Optional
import yaml
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

from src.utils import (
    get_hostname,
    get_cpu_temp,
    get_ram_usage,
    get_uptime,
    format_uptime
)


class OLEDMonitor:
    """Main application class for OLED monitoring service"""
    
    def __init__(self, config_path: str = "/etc/oled-monitor/config.yaml"):
        self.config_path = config_path
        self.config = None
        self.device = None
        self.running = True
        self.logger = None
        self.last_update = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        self.load_config()
    
    def setup_logging(self):
        """Configure logging with rotation"""
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "app.log"
        
        # Create logger
        self.logger = logging.getLogger("oled-monitor")
        self.logger.setLevel(logging._nameToLevel[self.config.log_level])
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def load_config(self) -> bool:
        """Load configuration from YAML file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logging.error(f"Config file not found: {self.config_path}")
                return False
            
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            
            logging.info(f"Configuration loaded from {self.config_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return False
    
    def init_display(self) -> bool:
        """Initialize OLED display"""
        try:
            i2c_bus = self.config['i2c']['bus']
            i2c_address = int(self.config['i2c']['address'])
            
            serial = i2c(port=i2c_bus, address=i2c_address)
            
            # Device settings based on config
            width = self.config['display']['width']
            height = self.config['display']['height']
            rotate = self.config['display']['rotate']

            self.device = ssd1306(
                serial,
                width=width,
                height=height,
                rotate=0
            )
            
            self.logger.info(f"Display initialized: {width}x{height} at 0x{i2c_address:02X}")
            
            # Clear display
            self.device.clear()
            self.device.display()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize display: {e}")
            return False
    
    def get_text_dimensions(self, text: str, font: ImageFont) -> tuple:
        """Get text dimensions using PIL"""
        if hasattr(font, 'getbbox'):
            # For newer PIL versions
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        else:
            # For older PIL versions
            return font.getsize(text)
    
    def draw_text_centered(self, draw, text: str, y: int, font: ImageFont, 
                           width: int = 128) -> tuple:
        """Draw text centered horizontally"""
        text_width, text_height = self.get_text_dimensions(text, font)
        x = (width - text_width) // 2
        draw.text((x, y), text, font=font, fill="white")
        return x, y + text_height
    
    def update_display(self):
        """Update OLED display with current system information"""
        try:
            # Get system information
            hostname = get_hostname()
            cpu_temp = get_cpu_temp()
            ram_usage, ram_total, ram_percent = get_ram_usage()
            uptime_seconds = get_uptime()
            uptime_str = format_uptime(uptime_seconds)
                        
            # Create image
            width = self.config['display']['width']
            height = self.config['display']['height']
            
            with canvas(self.device) as draw:
                # Clear background
                draw.rectangle((0, 0, width, height), outline=0, fill=0)
                
                # Try to load fonts with fallback
                try:
                    # Try to load system fonts
                    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
                    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
                except:
                    # Fallback to default PIL font
                    font_large = ImageFont.load_default()
                    font_small = ImageFont.load_default()
                
                # Line 1: Hostname (centered)
                self.draw_text_centered(draw, hostname[:20], 0, font_large, width)
                
                # Line 2: System info
                line2 = f"{cpu_temp:>3.0f}°C {ram_percent:>3.0f}% {uptime_str}"
                self.draw_text_centered(draw, line2, 12, font_small, width)
                
                # # Line 3: Network traffic
                # # Check if there's room for third line
                # line3 = f"{rx_str} {tx_str}"
                # line3_width, _ = self.get_text_dimensions(line3, font_small)
                # if line3_width <= width:
                #     self.draw_text_centered(draw, line3, 22, font_small, width)
                # else:
                #     # If too long, split into two lines
                #     rx_text = f"⬇{self.format_traffic(int(rx_speed if self.last_tx > 0 else rx_bytes))}/s"
                #     tx_text = f"⬆{self.format_traffic(int(tx_speed if self.last_tx > 0 else tx_bytes))}/s"
                #     self.draw_text_centered(draw, rx_text, 22, font_small, width)
                
                self.logger.debug(f"Display updated: {hostname} | Temp: {cpu_temp}°C | RAM: {ram_percent}% | Uptime: {uptime_str}")
            
        except Exception as e:
            self.logger.error(f"Failed to update display: {e}")
    
    def run(self):
        """Main application loop"""
        self.logger.info("Starting OLED Monitor service")
        
        # Load configuration
        if not self.load_config():
            self.logger.error("Failed to load configuration. Exiting.")
            sys.exit(1)
        
        # Initialize display
        if not self.init_display():
            self.logger.error("Failed to initialize display. Exiting.")
            sys.exit(1)
        
        # Get update interval from config
        update_interval = self.config.get('app', {}).get('update_interval', 2)
        
        self.logger.info(f"Update interval: {update_interval} seconds")
        self.logger.info("Service is running. Press Ctrl+C to stop.")
        
        # Main loop
        while self.running:
            try:
                self.update_display()
                time.sleep(update_interval)
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(5)
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        if self.device:
            self.device.clear()
            self.device.display()
        sys.exit(0)


def main():
    """Application entry point"""
    # Determine config path
    config_path = os.environ.get('CONFIG_PATH', '/etc/oled-monitor/config.yaml')
    
    # Create and run application
    app = OLEDMonitor(config_path)
    app.setup_logging()
    
    try:
        app.run()
    except KeyboardInterrupt:
        app.logger.info("Application stopped by user")
        sys.exit(0)
    except Exception as e:
        app.logger.error(f"Application crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()