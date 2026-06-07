"""
Process monitoring module for DGXTOP Ubuntu
Handles reading CPU, memory, and IO statistics for top processes using psutil
"""

import time
import psutil
from typing import List, Dict, Any


class ProcessMonitor:
    """Monitor top system processes using psutil"""

    def __init__(self):
        self.processes: Dict[int, psutil.Process] = {}
        self.prev_io: Dict[int, tuple] = {}  # pid -> (read_bytes, write_bytes, timestamp)

    def get_top_processes(self, limit: int = 8, sort_by: str = "cpu") -> List[Dict[str, Any]]:
        """Get top processes by CPU or Memory usage, calculating IO rates where possible"""
        current_pids = set()
        stats_list = []
        now = time.time()

        for proc in psutil.process_iter(attrs=['pid', 'name', 'username']):
            try:
                pid = proc.info['pid']
                current_pids.add(pid)

                # Get or cache Process object to persist cpu_percent state
                if pid not in self.processes:
                    self.processes[pid] = proc
                p = self.processes[pid]

                # Check if PID was recycled (create time differs)
                try:
                    p_create_time = p.create_time()
                    proc_create_time = proc.create_time()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    p_create_time = 0.0
                    proc_create_time = 0.0

                if p_create_time != proc_create_time:
                    self.processes[pid] = proc
                    p = proc

                # Query CPU and Memory
                try:
                    cpu_pct = p.cpu_percent(interval=None)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    cpu_pct = 0.0

                try:
                    mem_info = p.memory_info()
                    mem_rss = mem_info.rss
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    mem_rss = 0

                try:
                    mem_pct = p.memory_percent()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    mem_pct = 0.0

                # Get IO counters
                read_rate = 0.0
                write_rate = 0.0
                try:
                    io = p.io_counters()
                    read_bytes = io.read_bytes
                    write_bytes = io.write_bytes

                    if pid in self.prev_io:
                        prev_read, prev_write, prev_time = self.prev_io[pid]
                        dt = now - prev_time
                        if dt > 0:
                            read_rate = max(0.0, (read_bytes - prev_read) / dt)
                            write_rate = max(0.0, (write_bytes - prev_write) / dt)

                    self.prev_io[pid] = (read_bytes, write_bytes, now)
                except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                    # IO counters not available or access denied
                    pass

                stats_list.append({
                    "pid": pid,
                    "name": proc.info['name'] or "unknown",
                    "username": proc.info['username'] or "unknown",
                    "cpu_percent": cpu_pct,
                    "memory_percent": mem_pct,
                    "memory_rss": mem_rss,
                    "read_rate": read_rate,
                    "write_rate": write_rate,
                })

            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                continue

        # Clean up cache for dead processes
        self.processes = {pid: self.processes[pid] for pid in current_pids if pid in self.processes}
        self.prev_io = {pid: self.prev_io[pid] for pid in current_pids if pid in self.prev_io}

        # Sort
        if sort_by == "cpu":
            stats_list.sort(key=lambda x: x["cpu_percent"], reverse=True)
        elif sort_by == "memory":
            stats_list.sort(key=lambda x: x["memory_percent"], reverse=True)
        elif sort_by == "read":
            stats_list.sort(key=lambda x: x["read_rate"], reverse=True)
        elif sort_by == "write":
            stats_list.sort(key=lambda x: x["write_rate"], reverse=True)
        else:
            stats_list.sort(key=lambda x: x["cpu_percent"], reverse=True)

        return stats_list[:limit]
