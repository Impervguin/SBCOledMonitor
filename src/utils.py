#!/usr/bin/env python3
"""
System information utilities for OLED Monitor
"""

import os
import subprocess
import psutil
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

def get_cpu_percent() -> float:
    return psutil.cpu_percent(interval=None, percpu=False)


def get_ram_usage() -> Tuple[float, float, int]:
    """Get RAM usage in MB and percentage"""
    mem = psutil.virtual_memory()

    mem_used = mem.used / (1024 ** 2)
    mem_total = mem.total / (1024 ** 2)
    mem_percent = mem.percent
    
    return mem_used, mem_total, mem_percent


def format_ram_usage(ram: float, with_units: bool) -> str: # passed in MB
    units = "MB"
    if ram > 1024.0:
        ram /= 1024.0
        units = "GB"
    return f"{ram:3.1f}{units if with_units else ""}"



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
