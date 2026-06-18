#!/usr/bin/env python3
"""
System information utilities for OLED Monitor
"""

import os
import subprocess
import re
from datetime import datetime, timedelta
from typing import Tuple, Optional


def get_hostname() -> str:
    """Get system hostname"""
    try:
        return os.uname().nodename
    except:
        return "unknown"


def get_cpu_temp() -> float:
    """Get CPU temperature in Celsius"""
    temp_files = [
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/class/hwmon/hwmon0/temp1_input",
        "/sys/class/hwmon/hwmon1/temp1_input"
    ]
    
    for temp_file in temp_files:
        try:
            with open(temp_file, 'r') as f:
                temp = float(f.read().strip()) / 1000.0
                return temp
        except:
            continue
    
    return 0.0


def get_ram_usage() -> Tuple[float, float, int]:
    """Get RAM usage in MB and percentage"""
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        
        # Parse memory values (in kB)
        mem_total = int(re.search(r'MemTotal:\s+(\d+)\s+kB', meminfo).group(1)) / 1024.0  # MB
        mem_available = int(re.search(r'MemAvailable:\s+(\d+)\s+kB', meminfo).group(1)) / 1024.0  # MB
        mem_used = mem_total - mem_available
        mem_percent = int((mem_used / mem_total) * 100)
        
        return mem_used, mem_total, mem_percent
    except:
        return 0.0, 0.0, 0


def get_uptime() -> int:
    """Get system uptime in seconds"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.read().split()[0])
            return int(uptime_seconds)
    except:
        return 0


def format_uptime(seconds: int) -> str:
    """Format uptime seconds to human readable string"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h{minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d{hours}h"
