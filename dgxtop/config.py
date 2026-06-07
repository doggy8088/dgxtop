#!/usr/bin/env python3
"""Configuration management for DGXTOP Ubuntu"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ColorTheme:
    """Color theme for dashing components (0-8 color codes)"""

    name: str
    primary: int
    secondary: int
    warning: int
    critical: int


@dataclass
class AppConfig:
    """Application configuration"""

    update_interval: float = 1.0
    color_theme: str = "green"
    redline_threshold: float = 80.0
    history_length: int = 60
    log_level: str = "INFO"
    gpu_enabled: bool = True

    # Alerting thresholds
    cpu_threshold: float = 90.0
    gpu_threshold: float = 90.0
    mem_threshold: float = 90.0
    disk_await_threshold: float = 50.0  # ms

    # Process settings
    process_limit: int = 8
    process_sort_by: str = "cpu"  # cpu, memory, read, write

    # Network interface settings
    network_interfaces: list = None  # None/empty means auto-detect all physical
    network_interface_history: str = ""  # If specified, the sparkline shows only this interface

    # Logging settings
    log_dir: str = "/tmp/dgxtop_logs"
    log_file_enabled: bool = True

    def __post_init__(self):
        # Load from file first, if available
        self.load_from_file()
        # Save default configuration if it doesn't exist
        self.save_default_config()

    def load_from_file(self) -> bool:
        """Load settings from the first available configuration file"""
        import json
        import os

        config_paths = [
            os.path.join(os.getcwd(), "dgxtop.json"),
            os.path.expanduser("~/.config/dgxtop/config.json"),
            "/etc/dgxtop.json"
        ]

        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # Update fields dynamically
                    for k, v in data.items():
                        if hasattr(self, k):
                            setattr(self, k, v)
                    return True
                except Exception:
                    pass
        return False

    def save_default_config(self):
        """Save the default configuration to ~/.config/dgxtop/config.json if it doesn't exist"""
        import json
        import os

        path = os.path.expanduser("~/.config/dgxtop/config.json")
        if not os.path.exists(path):
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                data = {
                    "update_interval": self.update_interval,
                    "color_theme": self.color_theme,
                    "redline_threshold": self.redline_threshold,
                    "history_length": self.history_length,
                    "log_level": self.log_level,
                    "gpu_enabled": self.gpu_enabled,
                    "cpu_threshold": self.cpu_threshold,
                    "gpu_threshold": self.gpu_threshold,
                    "mem_threshold": self.mem_threshold,
                    "disk_await_threshold": self.disk_await_threshold,
                    "process_limit": self.process_limit,
                    "process_sort_by": self.process_sort_by,
                    "network_interfaces": self.network_interfaces,
                    "network_interface_history": self.network_interface_history,
                    "log_dir": self.log_dir,
                    "log_file_enabled": self.log_file_enabled,
                }
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except Exception:
                pass


COLOR_THEMES: Dict[str, ColorTheme] = {
    "green": ColorTheme("green", primary=2, secondary=2, warning=3, critical=1),
    "amber": ColorTheme("amber", primary=3, secondary=3, warning=1, critical=1),
    "blue": ColorTheme("blue", primary=4, secondary=6, warning=3, critical=1),
}

