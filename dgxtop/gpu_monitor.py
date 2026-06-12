#!/usr/bin/env python3
"""NVIDIA GPU monitoring via nvidia-smi for DGX SPARK"""

import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GPUStats:
    """Container for NVIDIA GPU statistics"""

    index: int
    name: str
    utilization_gpu: float  # 0-100%
    temperature: float  # Celsius
    power_draw: float  # Watts
    power_limit: float  # Watts
    fan_speed: Optional[float]  # % (may be N/A)
    clock_graphics: float = 0.0  # MHz - current graphics clock
    clock_max: float = 0.0  # MHz - max graphics clock


class GPUMonitor:
    """Monitor NVIDIA GPU statistics via nvidia-smi"""

    QUERY_FIELDS = (
        "index,name,utilization.gpu,"
        "temperature.gpu,power.draw,power.limit,fan.speed,"
        "clocks.current.graphics,clocks.max.graphics"
    )

    def __init__(self):
        self.last_stats: List[GPUStats] = []
        self._available = self._check_nvidia_smi()

    def _check_nvidia_smi(self) -> bool:
        """Check if nvidia-smi is available"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--version"], capture_output=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @property
    def is_available(self) -> bool:
        return self._available

    def get_stats(self) -> List[GPUStats]:
        """Query GPU statistics via nvidia-smi (one entry per GPU)"""
        if not self._available:
            return []

        try:
            cmd = [
                "nvidia-smi",
                f"--query-gpu={self.QUERY_FIELDS}",
                "--format=csv,noheader,nounits",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)

            if result.returncode != 0:
                return self.last_stats

            def safe_float(v, default=0.0):
                try:
                    return float(v) if v not in ["[N/A]", "N/A", ""] else default
                except (ValueError, TypeError):
                    return default

            def safe_int(v, default=0):
                try:
                    return int(float(v)) if v not in ["[N/A]", "N/A", ""] else default
                except (ValueError, TypeError):
                    return default

            stats_list: List[GPUStats] = []
            for line in result.stdout.strip().splitlines():
                if not line.strip():
                    continue
                values = [v.strip() for v in line.split(",")]
                if len(values) < 6:
                    continue

                stats_list.append(GPUStats(
                    index=safe_int(values[0]),
                    name=values[1].strip(),
                    utilization_gpu=safe_float(values[2]),
                    temperature=safe_float(values[3]),
                    power_draw=safe_float(values[4]),
                    power_limit=safe_float(values[5], default=100.0),
                    fan_speed=safe_float(values[6]) if len(values) > 6 else None,
                    clock_graphics=safe_float(values[7]) if len(values) > 7 else 0.0,
                    clock_max=safe_float(values[8]) if len(values) > 8 else 0.0,
                ))

            if stats_list:
                self.last_stats = stats_list
            return self.last_stats

        except Exception as e:
            # Log error for debugging but don't crash
            import sys
            print(f"GPU monitor error: {e}", file=sys.stderr)
            return self.last_stats
            return stats

        except Exception as e:
            # Log error for debugging but don't crash
            import sys
            print(f"GPU monitor error: {e}", file=sys.stderr)
            return self.last_stats
