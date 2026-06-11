#!/usr/bin/env python3
"""Main application for DGXTOP Ubuntu - DGX SPARK Edition

Uses rich library for SSH-compatible terminal UI.
"""

import time
import sys
import os
import signal
import select
import termios
import tty
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.live import Live
from rich.console import Console

from config import AppConfig
from gpu_monitor import GPUMonitor
from system_monitor import SystemMonitor
from disk_monitor import DiskMonitor
from network_monitor import NetworkMonitor
from process_monitor import ProcessMonitor
from rich_ui import RichUI
from logger import get_logger, log_system_info


class DGXTop:
    """Main DGXTOP application for DGX SPARK"""

    def __init__(self, config: AppConfig = None, daemon_mode: bool = False):
        self.config = config if config is not None else AppConfig()
        self.config.daemon_mode = daemon_mode
        self.console = Console()
        self.gpu_monitor = GPUMonitor()
        self.system_monitor = SystemMonitor()
        self.disk_monitor = DiskMonitor()
        self.network_monitor = NetworkMonitor(self.config)
        self.process_monitor = ProcessMonitor()
        self.ui = RichUI(self.config)
        
        # Configure logging directory and level from AppConfig
        self.logger = get_logger(self.config.log_dir, self.config.log_level)
        self.running = True

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        log_system_info()
        self.logger.log_info("DGXTOP DGX SPARK initialized")

    def _handle_signal(self, signum, frame):
        """Handle termination signals gracefully"""
        self.running = False

    def _check_keyboard(self) -> str | None:
        """Check for keyboard input without blocking"""
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None

    def _handle_key(self, key: str):
        """Handle keyboard input"""
        if key == 'q' or key == '\x04':
            self.running = False
        elif key == '+' or key == '=':
            # Speed up (decrease interval), minimum 1.0 seconds
            self.config.update_interval = max(1.0, self.config.update_interval - 1.0)
        elif key == '-':
            # Slow down (increase interval), no upper limit
            self.config.update_interval = self.config.update_interval + 1.0
        elif key == 'c':
            self.config.process_sort_by = "cpu"
        elif key == 'm':
            self.config.process_sort_by = "memory"
        elif key == 'r':
            self.config.process_sort_by = "read"
        elif key == 'w':
            self.config.process_sort_by = "write"
        elif key == 'h':
            self.ui.show_help = not self.ui.show_help

    def collect_stats(self) -> dict:
        """Collect all system statistics"""
        stats = self.system_monitor.get_stats()

        # GPU stats
        gpu_stats = self.gpu_monitor.get_stats()
        if gpu_stats:
            stats["gpu"] = gpu_stats

        # Disk stats with latency
        disk_stats = self.disk_monitor.get_device_stats_for_display()
        stats["disk"] = disk_stats

        # Disk history for sparklines
        stats["disk_history"] = self.disk_monitor.get_history()

        # Network stats
        network_stats = self.network_monitor.get_interface_stats_for_display()
        stats["network_io"] = network_stats

        # Network history for sparklines
        stats["network_history"] = self.network_monitor.get_history()

        # Process stats
        process_stats = self.process_monitor.get_top_processes(
            limit=self.config.process_limit,
            sort_by=self.config.process_sort_by
        )
        stats["processes"] = process_stats

        return stats

    def run(self):
        """Main application loop using rich Live display or daemon loop"""
        if getattr(self.config, "daemon_mode", False):
            self.logger.log_info("Starting daemon loop")
            try:
                while self.running:
                    start = time.time()
                    try:
                        stats = self.collect_stats()
                        self.logger.log_performance_stats(stats)
                    except Exception as e:
                        self.logger.log_error(e, "Daemon stats collection")

                    elapsed = time.time() - start
                    sleep_time = max(0, self.config.update_interval - elapsed)
                    time.sleep(sleep_time)
            except KeyboardInterrupt:
                pass
            finally:
                self.logger.log_info("DGXTOP daemon shutdown")
            return

        self.logger.log_info("Starting main loop")

        # Check if we have a TTY for keyboard input
        has_tty = sys.stdin.isatty()
        old_settings = None

        if has_tty:
            # Save terminal settings and set to raw mode for keyboard input
            old_settings = termios.tcgetattr(sys.stdin)

        try:
            if has_tty:
                tty.setcbreak(sys.stdin.fileno())

            # Use rich Live for real-time updates
            with Live(
                self.ui.get_renderable({}),
                console=self.console,
                refresh_per_second=1,
                screen=True,  # Use alternate screen buffer
            ) as live:
                while self.running:
                    start = time.time()

                    try:
                        # Check for keyboard input (only if TTY available)
                        if has_tty:
                            key = self._check_keyboard()
                            if key:
                                self._handle_key(key)

                        # Collect stats
                        stats = self.collect_stats()

                        # Log stats at debug level (or if logging enabled)
                        self.logger.log_performance_stats(stats)

                        # Update the live display
                        live.update(self.ui.get_renderable(stats))

                    except Exception as e:
                        self.logger.log_error(e, "Stats collection")

                    # Maintain update interval, but check keyboard frequently for instant response
                    elapsed = time.time() - start
                    sleep_time = max(0, self.config.update_interval - elapsed)
                    
                    step = 0.05
                    slept = 0.0
                    while slept < sleep_time and self.running:
                        if has_tty:
                            key = self._check_keyboard()
                            if key:
                                self._handle_key(key)
                                # Update UI instantly on key press using cached stats
                                live.update(self.ui.get_renderable(stats))
                                # Recalculate remaining sleep time
                                elapsed = time.time() - start
                                sleep_time = max(0, self.config.update_interval - elapsed)
                        time.sleep(min(step, max(0.0, sleep_time - slept)))
                        slept += step

        except KeyboardInterrupt:
            pass
        finally:
            # Restore terminal settings if we modified them
            if has_tty and old_settings:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            self.logger.log_info("DGXTOP shutdown")


def install_systemd_service(user_level: bool = False):
    """Install systemd service file"""
    import subprocess

    executable = sys.executable
    script_path = os.path.abspath(__file__)
    
    # ExecStart will point to the python3 script_path --daemon
    exec_start = f"{executable} {script_path} --daemon"

    service_content = f"""[Unit]
Description=DGXTOP System Monitor Service
After=network.target

[Service]
Type=simple
ExecStart={exec_start}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
""" if user_level else f"""[Unit]
Description=DGXTOP System Monitor Service
After=network.target

[Service]
Type=simple
ExecStart={exec_start}
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
"""

    if user_level:
        service_dir = os.path.expanduser("~/.config/systemd/user")
        os.makedirs(service_dir, exist_ok=True)
        service_path = os.path.join(service_dir, "dgxtop.service")
        
        try:
            with open(service_path, "w", encoding="utf-8") as f:
                f.write(service_content)
            print(f"User service file created at: {service_path}")
            
            # Reload daemon and enable
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "--user", "enable", "dgxtop.service"], check=True)
            subprocess.run(["systemctl", "--user", "start", "dgxtop.service"], check=True)
            print("Successfully installed and started dgxtop user-level service!")
        except Exception as e:
            print(f"Error installing user-level service: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        service_path = "/etc/systemd/system/dgxtop.service"
        print("Writing system-wide systemd service file...")
        
        try:
            import tempfile
            with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
                tmp.write(service_content)
                tmp_path = tmp.name
            
            # Move file using sudo
            subprocess.run(["sudo", "mv", tmp_path, service_path], check=True)
            subprocess.run(["sudo", "chown", "root:root", service_path], check=True)
            subprocess.run(["sudo", "chmod", "644", service_path], check=True)
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", "dgxtop.service"], check=True)
            subprocess.run(["sudo", "systemctl", "start", "dgxtop.service"], check=True)
            print("Successfully installed and started dgxtop system-level service!")
        except Exception as e:
            print(f"Error installing system-wide service: {e}", file=sys.stderr)
            print("Please run this command with sudo / as root, or try --install-user-service")
            sys.exit(1)


def main():
    """Entry point"""
    try:
        from dgxtop import __version__
    except ImportError:
        try:
            from __init__ import __version__
        except ImportError:
            __version__ = "1.0.0"

    parser = argparse.ArgumentParser(
        prog="dgxtop",
        description="System monitor for NVIDIA DGX Spark - real-time CPU, GPU, memory, disk, and network monitoring",
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Update interval in seconds",
    )
    parser.add_argument(
        "-d", "--daemon",
        action="store_true",
        help="Run in daemon mode (background monitoring & logging)",
    )
    parser.add_argument(
        "--install-service",
        action="store_true",
        help="Install systemd service system-wide",
    )
    parser.add_argument(
        "--install-user-service",
        action="store_true",
        help="Install systemd service for current user",
    )
    parser.add_argument(
        "-n", "--interface",
        type=str,
        help="Monitor specific network interface",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set log level",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        help="Directory to save logs",
    )
    parser.add_argument(
        "--sort-processes",
        type=str,
        choices=["cpu", "memory", "read", "write"],
        help="Process list sorting",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"dgxtop {__version__}",
    )

    args = parser.parse_args()

    # Handle service installations immediately
    if args.install_service:
        install_systemd_service(user_level=False)
        sys.exit(0)
    elif args.install_user_service:
        install_systemd_service(user_level=True)
        sys.exit(0)

    console = Console()

    try:
        config = AppConfig()
        
        # Override config settings from CLI arguments if provided
        if args.interval is not None:
            config.update_interval = args.interval
        if args.interface is not None:
            config.network_interfaces = [args.interface]
            config.network_interface_history = args.interface
        if args.log_level is not None:
            config.log_level = args.log_level
        if args.log_dir is not None:
            config.log_dir = args.log_dir
        if args.sort_processes is not None:
            config.process_sort_by = args.sort_processes

        app = DGXTop(config=config, daemon_mode=args.daemon)
        app.run()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
