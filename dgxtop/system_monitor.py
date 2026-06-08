"""
System monitoring module for DGXTOP Ubuntu
Handles CPU, memory, and network statistics
"""

import time
import os
from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class MemoryStats:
    """Container for memory statistics"""

    total: int
    used: int
    free: int
    buffers: int
    cached: int
    usage_percent: float


@dataclass
class CPUStats:
    """Container for CPU statistics"""

    usage_percent: float
    user_time: float
    system_time: float
    idle_time: float
    iowait_time: float
    frequency_mhz: float = 0.0
    frequency_max_mhz: float = 0.0
    temperature_celsius: float = 0.0
    core_count: int = field(default_factory=lambda: os.cpu_count() or 1)


@dataclass
class NetworkStats:
    """Container for network statistics"""

    bytes_recv: int
    bytes_sent: int
    packets_recv: int
    packets_sent: int


class SystemMonitor:
    """Monitor system statistics from /proc files"""

    def __init__(self):
        self.cpu_stats: Dict[str, float] = {}
        self.memory_stats = MemoryStats(0, 0, 0, 0, 0, 0)
        self.network_stats = NetworkStats(0, 0, 0, 0)
        self.previous_network_stats = NetworkStats(0, 0, 0, 0)
        self.last_network_update = time.time()
        # Store previous CPU times for delta calculation
        self._prev_cpu_times: Dict[str, float] = {}

    def _read_cpu_times(self) -> Dict[str, float]:
        """Read raw CPU times from /proc/stat"""
        cpu_path = "/proc/stat"
        try:
            with open(cpu_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("cpu "):
                        parts = line.split()
                        if len(parts) >= 5:
                            return {
                                "user": float(parts[1]),
                                "nice": float(parts[2]),
                                "system": float(parts[3]),
                                "idle": float(parts[4]),
                                "iowait": float(parts[5]) if len(parts) > 5 else 0.0,
                                "irq": float(parts[6]) if len(parts) > 6 else 0.0,
                                "softirq": float(parts[7]) if len(parts) > 7 else 0.0,
                            }
        except IOError:
            pass
        return {}

    def _parse_cpu_stats(self) -> CPUStats:
        """Parse CPU statistics from /proc/stat using delta calculation"""
        current_times = self._read_cpu_times()
        if not current_times:
            return CPUStats(0, 0, 0, 0, 0)

        # Calculate usage from delta if we have previous data
        if self._prev_cpu_times:
            # Calculate deltas
            user_delta = current_times["user"] - self._prev_cpu_times.get("user", 0)
            nice_delta = current_times["nice"] - self._prev_cpu_times.get("nice", 0)
            system_delta = current_times["system"] - self._prev_cpu_times.get("system", 0)
            idle_delta = current_times["idle"] - self._prev_cpu_times.get("idle", 0)
            iowait_delta = current_times["iowait"] - self._prev_cpu_times.get("iowait", 0)
            irq_delta = current_times["irq"] - self._prev_cpu_times.get("irq", 0)
            softirq_delta = current_times["softirq"] - self._prev_cpu_times.get("softirq", 0)

            # Total time delta
            total_delta = (user_delta + nice_delta + system_delta + idle_delta +
                          iowait_delta + irq_delta + softirq_delta)

            # Calculate usage percent from delta
            if total_delta > 0:
                usage_percent = ((total_delta - idle_delta - iowait_delta) / total_delta) * 100
            else:
                usage_percent = 0.0
        else:
            # First call - no previous data, return 0
            usage_percent = 0.0
            user_delta = 0.0
            system_delta = 0.0
            idle_delta = 0.0
            iowait_delta = 0.0

        # Store current times for next call
        self._prev_cpu_times = current_times

        # Get frequency and temperature
        current_freq, max_freq = self._get_cpu_frequency()
        temperature = self._get_cpu_temperature()

        return CPUStats(
            usage_percent=usage_percent,
            user_time=current_times["user"],
            system_time=current_times["system"],
            idle_time=current_times["idle"],
            iowait_time=current_times["iowait"],
            frequency_mhz=current_freq,
            frequency_max_mhz=max_freq,
            temperature_celsius=temperature,
            core_count=os.cpu_count() or 1,
        )

    def _parse_memory_stats(self) -> MemoryStats:
        """Parse memory statistics from /proc/meminfo"""
        meminfo_path = "/proc/meminfo"

        try:
            with open(meminfo_path, "r") as f:
                lines = f.readlines()

            meminfo = {}
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    # Extract numeric value and unit
                    if " " in value:
                        num_str, unit = value.split(" ", 1)
                        try:
                            num = int(num_str)
                            if unit == "kB":
                                num *= 1024
                            meminfo[key] = num
                        except ValueError:
                            continue
                    else:
                        try:
                            meminfo[key] = int(value)
                        except ValueError:
                            continue

            # Calculate memory usage
            total = meminfo.get("MemTotal", 0)
            free = meminfo.get("MemFree", 0)
            buffers = meminfo.get("Buffers", 0)
            cached = meminfo.get("Cached", 0)

            used = total - free - buffers - cached
            if used < 0:
                used = total - free

            usage_percent = (used / total) * 100 if total > 0 else 0

            return MemoryStats(
                total=total,
                used=used,
                free=free,
                buffers=buffers,
                cached=cached,
                usage_percent=usage_percent,
            )

        except IOError:
            pass

        return MemoryStats(0, 0, 0, 0, 0, 0)

    def _parse_network_stats(self) -> NetworkStats:
        """Parse network statistics from /proc/net/dev"""
        netdev_path = "/proc/net/dev"

        try:
            with open(netdev_path, "r") as f:
                lines = f.readlines()

            bytes_recv = 0
            bytes_sent = 0
            packets_recv = 0
            packets_sent = 0

            # Skip header lines
            for line in lines[2:]:
                line = line.strip()
                if ":" in line:
                    interface, stats = line.split(":", 1)
                    interface = interface.strip()

                    # Skip loopback
                    if interface == "lo":
                        continue

                    parts = stats.split()
                    if len(parts) >= 16:
                        try:
                            bytes_recv += int(parts[1])
                            packets_recv += int(parts[2])
                            bytes_sent += int(parts[9])
                            packets_sent += int(parts[10])
                        except (ValueError, IndexError):
                            continue

            return NetworkStats(
                bytes_recv=bytes_recv,
                bytes_sent=bytes_sent,
                packets_recv=packets_recv,
                packets_sent=packets_sent,
            )

        except IOError:
            pass

        return NetworkStats(0, 0, 0, 0)

    def _get_cpu_frequency(self) -> tuple:
        """Get current and max CPU frequency in MHz"""
        try:
            freq_sum = 0
            cpu_count = 0

            for cpu_id in range(os.cpu_count() or 1):
                freq_path = (
                    f"/sys/devices/system/cpu/cpu{cpu_id}/cpufreq/scaling_cur_freq"
                )
                if os.path.exists(freq_path):
                    with open(freq_path, "r") as f:
                        freq_sum += int(f.read().strip()) / 1000  # kHz to MHz
                        cpu_count += 1

            current = freq_sum / cpu_count if cpu_count > 0 else 0.0

            max_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq"
            with open(max_path, "r") as f:
                max_freq = int(f.read().strip()) / 1000

            return current, max_freq
        except (IOError, ValueError):
            return 0.0, 0.0

    def _get_cpu_temperature(self) -> float:
        """Get CPU temperature in Celsius"""
        try:
            for zone_id in range(10):
                temp_path = f"/sys/class/thermal/thermal_zone{zone_id}/temp"
                type_path = f"/sys/class/thermal/thermal_zone{zone_id}/type"

                if os.path.exists(temp_path) and os.path.exists(type_path):
                    with open(type_path, "r") as f:
                        zone_type = f.read().strip().lower()

                    if "cpu" in zone_type or "soc" in zone_type:
                        with open(temp_path, "r") as f:
                            return int(f.read().strip()) / 1000

            # Fallback to zone 0
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return int(f.read().strip()) / 1000
        except (IOError, ValueError):
            return 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        cpu = self._parse_cpu_stats()
        memory = self._parse_memory_stats()
        network = self._parse_network_stats()

        # Calculate network rates
        current_time = time.time()
        time_delta = current_time - self.last_network_update

        if time_delta > 0 and self.previous_network_stats.bytes_recv > 0:
            recv_rate = (
                network.bytes_recv - self.previous_network_stats.bytes_recv
            ) / time_delta
            send_rate = (
                network.bytes_sent - self.previous_network_stats.bytes_sent
            ) / time_delta
        else:
            recv_rate = 0
            send_rate = 0

        # Update previous stats
        self.previous_network_stats = network
        self.last_network_update = current_time

        return {
            "cpu": cpu,
            "memory": memory,
            "network": {
                "stats": network,
                "recv_rate": recv_rate,
                "send_rate": send_rate,
            },
        }

    def format_memory(self, bytes_val: int) -> str:
        """Format bytes with appropriate unit"""
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024**2:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024**3:
            return f"{bytes_val / 1024**2:.1f} MB"
        else:
            return f"{bytes_val / 1024**3:.1f} GB"

    def format_network_rate(self, rate: float) -> str:
        """Format network rate with appropriate unit"""
        if rate < 1024:
            return f"{rate:.1f} B/s"
        elif rate < 1024**2:
            return f"{rate / 1024:.1f} KB/s"
        elif rate < 1024**3:
            return f"{rate / 1024**2:.1f} MB/s"
        else:
            return f"{rate / 1024**3:.1f} GB/s"
