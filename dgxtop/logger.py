"""
Logging module for DGXTOP Ubuntu
Comprehensive logging system for triage and debugging
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional
import threading


class DGXTopLogger:
    """Comprehensive logging system for DGXTOP Ubuntu"""

    def __init__(self, log_dir: str = "/tmp/dgxtop_logs", log_level: str = "INFO"):
        self.log_dir = log_dir
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup comprehensive logging system"""
        # Create log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)

        # Create logger
        logger = logging.getLogger("dgxtop")
        logger.setLevel(self.log_level)

        # Clear existing handlers
        logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )

        simple_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )

        # File handler for detailed logs
        log_file = os.path.join(
            self.log_dir, f"dgxtop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

        # Console handler for real-time output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

        # Error file handler for errors only
        error_file = os.path.join(
            self.log_dir,
            f"dgxtop_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        )
        error_handler = logging.FileHandler(error_file, mode="a", encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)

        return logger

    def log_system_info(self):
        """Log system information"""
        import platform
        import psutil

        self.logger.info("=== System Information ===")
        self.logger.info(f"Platform: {platform.platform()}")
        self.logger.info(f"Architecture: {platform.machine()}")
        self.logger.info(f"Python Version: {platform.python_version()}")
        self.logger.info(f"CPU Cores: {psutil.cpu_count()}")
        self.logger.info(
            f"Memory Total: {psutil.virtual_memory().total / (1024**3):.2f} GB"
        )
        self.logger.info(f"Boot Time: {datetime.fromtimestamp(psutil.boot_time())}")
        self.logger.info("=========================")

    def log_performance_stats(self, stats: dict):
        """Log performance statistics"""
        self.logger.debug("=== Performance Statistics ===")
        if "cpu" in stats:
            cpu = stats["cpu"]
            self.logger.debug(f"CPU Usage: {cpu.usage_percent:.2f}%")
            self.logger.debug(f"CPU User Time: {cpu.user_time:.2f}%")
            self.logger.debug(f"CPU System Time: {cpu.system_time:.2f}%")
            self.logger.debug(f"CPU I/O Wait: {cpu.iowait_time:.2f}%")

        if "memory" in stats:
            memory = stats["memory"]
            self.logger.debug(f"Memory Usage: {memory.usage_percent:.2f}%")
            self.logger.debug(f"Memory Used: {memory.used / (1024**3):.2f} GB")
            self.logger.debug(f"Memory Free: {memory.free / (1024**3):.2f} GB")

        if "network" in stats:
            network = stats["network"]
            self.logger.debug(f"Network RX Rate: {network['recv_rate']:.2f} B/s")
            self.logger.debug(f"Network TX Rate: {network['send_rate']:.2f} B/s")

        if "disk" in stats:
            disk_stats = stats["disk"]
            for device, stat in disk_stats.items():
                self.logger.debug(
                    f"Disk {device}: RX={stat.get('read_rate', 0.0):.2f} B/s, "
                    f"TX={stat.get('write_rate', 0.0):.2f} B/s"
                )

        self.logger.debug("==============================")

    def log_disk_operation(
        self, operation: str, device: str, bytes_count: int, duration: float
    ):
        """Log disk operations"""
        self.logger.info(
            f"Disk {operation} - Device: {device}, Bytes: {bytes_count}, "
            f"Duration: {duration:.4f}s, Rate: {bytes_count / duration:.2f} B/s"
        )

    def log_error(self, error: Exception, context: str = ""):
        """Log errors with context"""
        self.logger.error(f"Error in {context}: {type(error).__name__}: {str(error)}")
        import traceback

        self.logger.error(f"Traceback: {traceback.format_exc()}")

    def log_warning(self, message: str):
        """Log warnings"""
        self.logger.warning(message)

    def log_info(self, message: str):
        """Log info messages"""
        self.logger.info(message)

    def log_debug(self, message: str):
        """Log debug messages"""
        self.logger.debug(message)

    def get_log_files(self) -> list:
        """Get list of log files"""
        log_files = []
        if os.path.exists(self.log_dir):
            for file in os.listdir(self.log_dir):
                if file.startswith("dgxtop_") and file.endswith(".log"):
                    log_files.append(os.path.join(self.log_dir, file))
        return sorted(log_files)

    def cleanup_old_logs(self, days: int = 7):
        """Clean up old log files"""
        import glob
        import time

        cutoff_time = time.time() - (days * 24 * 60 * 60)
        log_files = glob.glob(os.path.join(self.log_dir, "dgxtop_*.log"))

        for log_file in log_files:
            if os.path.getmtime(log_file) < cutoff_time:
                try:
                    os.remove(log_file)
                    self.logger.info(f"Cleaned up old log file: {log_file}")
                except OSError as e:
                    self.logger.error(f"Failed to clean up log file {log_file}: {e}")


# Global logger instance
_logger_instance: Optional[DGXTopLogger] = None
_lock = threading.Lock()


def get_logger(
    log_dir: str = "/tmp/dgxtop_logs", log_level: str = "INFO"
) -> DGXTopLogger:
    """Get or create the global logger instance"""
    global _logger_instance

    with _lock:
        if _logger_instance is None:
            _logger_instance = DGXTopLogger(log_dir, log_level)

    return _logger_instance


def log_system_info():
    """Log system information using global logger"""
    logger = get_logger()
    logger.log_system_info()


def log_performance_stats(stats: dict):
    """Log performance statistics using global logger"""
    logger = get_logger()
    logger.log_performance_stats(stats)


def log_error(error: Exception, context: str = ""):
    """Log error using global logger"""
    logger = get_logger()
    logger.log_error(error, context)


def log_info(message: str):
    """Log info message using global logger"""
    logger = get_logger()
    logger.log_info(message)


def log_warning(message: str):
    """Log warning message using global logger"""
    logger = get_logger()
    logger.log_warning(message)


def log_debug(message: str):
    """Log debug message using global logger"""
    logger = get_logger()
    logger.log_debug(message)
