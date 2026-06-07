#!/usr/bin/env python3
"""Rich-based UI manager for DGXTOP Ubuntu - works reliably over SSH"""

import os
import sys
from collections import deque
from typing import Any, Dict, Optional

from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import AppConfig

# Sparkline characters for history graphs
SPARK_CHARS = "▁▂▃▄▅▆▇█"


class RichUI:
    """Manages the rich-based terminal UI for DGXTOP"""

    # Color themes matching asitop style
    THEMES = {
        "green": {
            "primary": "green",
            "bar_complete": "green",
            "bar_empty": "bright_black",
        },
        "amber": {
            "primary": "yellow",
            "bar_complete": "yellow",
            "bar_empty": "bright_black",
        },
        "blue": {
            "primary": "cyan",
            "bar_complete": "cyan",
            "bar_empty": "bright_black",
        },
    }

    def __init__(self, config: AppConfig):
        self.config = config
        self.console = Console()
        self.theme = self.THEMES.get(config.color_theme, self.THEMES["green"])

        # History for sparklines (keep last 40 values for width)
        self.cpu_history: deque = deque(maxlen=40)
        self.gpu_history: deque = deque(maxlen=40)
        self.mem_history: deque = deque(maxlen=40)
        self.disk_read_history: deque = deque(maxlen=40)
        self.disk_write_history: deque = deque(maxlen=40)

    def set_theme(self, theme_name: str):
        """Switch color theme"""
        if theme_name in self.THEMES:
            self.config.color_theme = theme_name
            self.theme = self.THEMES[theme_name]

    def _make_bar(self, percent: float, width: int = 20) -> Text:
        """Create a progress bar using block characters"""
        filled = int(width * percent / 100)
        empty = width - filled

        bar = Text()
        bar.append("█" * filled, style=self.theme["bar_complete"])
        bar.append("░" * empty, style=self.theme["bar_empty"])
        return bar

    def _make_sparkline(self, values: deque, max_val: Optional[float] = None) -> str:
        """Create a sparkline from historical values"""
        if not values:
            return ""

        if max_val is None or max_val == 0:
            max_val = max(values) if max(values) > 0 else 1

        sparkline = ""
        for v in values:
            # Normalize to 0-7 index with better resolution
            # Use 8 levels (0-7) and round to nearest for better visibility
            if max_val > 0 and v > 0:
                # Scale to 0-7, use round() for better distribution
                idx = min(7, round((v / max_val) * 7))
                # Ensure non-zero values show at least level 1
                idx = max(1, idx) if v > 0 else 0
            else:
                idx = 0
            sparkline += SPARK_CHARS[idx]

        return sparkline

    def _build_cpu_panel(self, stats: Dict[str, Any]) -> Panel:
        """Build CPU panel with usage bar and info"""
        cpu = stats.get("cpu")
        if not cpu:
            return Panel("No CPU data", title="CPU", border_style=self.theme["primary"])

        # Add to history
        self.cpu_history.append(cpu.usage_percent)

        # Build content
        lines = []

        # Usage line with bar
        bar = self._make_bar(cpu.usage_percent, 25)
        usage_text = Text()
        usage_text.append(
            f"Usage: {cpu.usage_percent:5.1f}% ", style=self.theme["primary"]
        )
        usage_text.append("[")
        usage_text.append(bar)
        usage_text.append("]")
        lines.append(usage_text)

        # Temperature
        temp_text = Text()
        temp_text.append(
            f"Temp:  {cpu.temperature_celsius:5.1f}°C", style=self.theme["primary"]
        )
        lines.append(temp_text)

        # Frequency (current / max)
        freq_text = Text()
        freq_text.append(
            f"Freq:  {cpu.frequency_mhz:5.0f} / 4800 MHz",
            style=self.theme["primary"],
        )
        lines.append(freq_text)

        # Sparkline history
        spark = self._make_sparkline(self.cpu_history, 100)
        spark_text = Text()
        spark_text.append(f"History: ", style="dim")
        spark_text.append(spark, style=self.theme["primary"])
        lines.append(spark_text)

        content = Group(*lines)
        return Panel(
            content,
            title=f"[bold]CPU ({cpu.core_count}-core ARM)[/bold]",
            border_style=self.theme["primary"],
            padding=(0, 1),
        )

    def _build_gpu_panel(self, stats: Dict[str, Any]) -> Panel:
        """Build GPU panel with usage, temp, power"""
        gpu = stats.get("gpu")
        if not gpu:
            return Panel(
                Text("nvidia-smi not available", style="dim"),
                title="GPU (Blackwell)",
                border_style=self.theme["primary"],
                padding=(0, 1),
            )

        # Add to history
        self.gpu_history.append(gpu.utilization_gpu)

        lines = []

        # GPU usage bar
        bar = self._make_bar(gpu.utilization_gpu, 25)
        usage_text = Text()
        usage_text.append(
            f"Usage: {gpu.utilization_gpu:5.1f}% ", style=self.theme["primary"]
        )
        usage_text.append("[")
        usage_text.append(bar)
        usage_text.append("]")
        lines.append(usage_text)

        # Temperature
        temp_text = Text()
        temp_text.append(
            f"Temp:  {gpu.temperature:5.1f}°C", style=self.theme["primary"]
        )
        lines.append(temp_text)

        # Frequency
        freq_text = Text()
        if gpu.clock_max > 0:
            freq_text.append(
                f"Freq:  {gpu.clock_graphics:5.0f} / {gpu.clock_max:.0f} MHz",
                style=self.theme["primary"],
            )
        else:
            freq_text.append(
                f"Freq:  {gpu.clock_graphics:5.0f} MHz",
                style=self.theme["primary"],
            )
        lines.append(freq_text)

        # Power
        power_text = Text()
        power_text.append(
            f"Power: {gpu.power_draw:5.1f}W / {gpu.power_limit:.0f}W",
            style=self.theme["primary"],
        )
        lines.append(power_text)

        # Sparkline history
        spark = self._make_sparkline(self.gpu_history, 100)
        spark_text = Text()
        spark_text.append("History: ", style="dim")
        spark_text.append(spark, style=self.theme["primary"])
        lines.append(spark_text)

        content = Group(*lines)
        return Panel(
            content,
            title=f"[bold]GPU ({gpu.name})[/bold]"
            if gpu.name
            else "[bold]GPU (Blackwell)[/bold]",
            border_style=self.theme["primary"],
            padding=(0, 1),
        )

    def _build_memory_panel(self, stats: Dict[str, Any]) -> Panel:
        """Build memory panel"""
        mem = stats.get("memory")
        if not mem:
            return Panel(
                "No memory data", title="Memory", border_style=self.theme["primary"]
            )

        # Add to history
        self.mem_history.append(mem.usage_percent)

        used_gb = mem.used / (1024**3)
        total_gb = mem.total / (1024**3)

        lines = []

        # Usage bar
        bar = self._make_bar(mem.usage_percent, 30)
        usage_text = Text()
        usage_text.append(
            f"RAM: {used_gb:5.1f} / {total_gb:.0f} GB ", style=self.theme["primary"]
        )
        usage_text.append("[")
        usage_text.append(bar)
        usage_text.append(f"] {mem.usage_percent:.1f}%")
        lines.append(usage_text)

        # Sparkline
        spark = self._make_sparkline(self.mem_history, 100)
        spark_text = Text()
        spark_text.append("History: ", style="dim")
        spark_text.append(spark, style=self.theme["primary"])
        lines.append(spark_text)

        content = Group(*lines)
        return Panel(
            content,
            title="[bold]Unified Memory[/bold]",
            border_style=self.theme["primary"],
            padding=(0, 1),
        )

    def _build_disk_history_panel(self, stats: Dict[str, Any]) -> Panel:
        """Build disk history sparklines panel"""
        disk_history = stats.get("disk_history", {})

        # Update history
        if disk_history.get("read"):
            # Convert to MB/s for display
            read_mb = (
                disk_history["read"][-1] / (1024 * 1024) if disk_history["read"] else 0
            )
            self.disk_read_history.append(read_mb)
        if disk_history.get("write"):
            write_mb = (
                disk_history["write"][-1] / (1024 * 1024)
                if disk_history["write"]
                else 0
            )
            self.disk_write_history.append(write_mb)

        lines = []

        # Read sparkline
        read_spark = self._make_sparkline(self.disk_read_history)
        read_text = Text()
        read_text.append("Read:  ", style="dim")
        read_text.append(read_spark, style=self.theme["primary"])
        if self.disk_read_history:
            read_text.append(
                f" {self.disk_read_history[-1]:.1f} MiB/s", style=self.theme["primary"]
            )
        lines.append(read_text)

        # Write sparkline
        write_spark = self._make_sparkline(self.disk_write_history)
        write_text = Text()
        write_text.append("Write: ", style="dim")
        write_text.append(write_spark, style=self.theme["primary"])
        if self.disk_write_history:
            write_text.append(
                f" {self.disk_write_history[-1]:.1f} MiB/s", style=self.theme["primary"]
            )
        lines.append(write_text)

        content = Group(*lines)
        return Panel(
            content,
            title="[bold]Disk History[/bold]",
            border_style=self.theme["primary"],
            padding=(0, 1),
        )

    def _build_disk_table(self, stats: Dict[str, Any]) -> Panel:
        """Build disk I/O statistics table"""
        disk_stats = stats.get("disk", {})

        table = Table(
            show_header=True,
            header_style=f"bold {self.theme['primary']}",
            border_style=self.theme["primary"],
            box=None,
            padding=(0, 1),
        )

        table.add_column("Device", style="bold")
        table.add_column("Read MiB/s", justify="right")
        table.add_column("Write MiB/s", justify="right")
        table.add_column("R-IOPS", justify="right")
        table.add_column("W-IOPS", justify="right")
        table.add_column("Await(ms)", justify="right")

        for device, stat in disk_stats.items():
            read_mb = stat.get("read_rate", 0) / (1024 * 1024)
            write_mb = stat.get("write_rate", 0) / (1024 * 1024)
            r_iops = stat.get("r_iops", 0)
            w_iops = stat.get("w_iops", 0)
            await_ms = stat.get("await_ms", 0)

            table.add_row(
                device,
                f"{read_mb:.2f}",
                f"{write_mb:.2f}",
                f"{r_iops:.0f}",
                f"{w_iops:.0f}",
                f"{await_ms:.2f}",
            )

        if not disk_stats:
            table.add_row("No devices", "-", "-", "-", "-", "-")

        return Panel(
            table,
            title="[bold]Disk I/O Statistics[/bold]",
            border_style=self.theme["primary"],
            padding=(0, 1),
        )

    def _build_network_table(self, stats: Dict[str, Any]) -> Panel:
        """Build network I/O statistics table"""
        network_stats = stats.get("network_io", {})

        table = Table(
            show_header=True,
            header_style=f"bold {self.theme['primary']}",
            border_style=self.theme["primary"],
            box=None,
            padding=(0, 1),
        )

        table.add_column("Interface", style="bold")
        table.add_column("RX MiB/s", justify="right")
        table.add_column("TX MiB/s", justify="right")
        table.add_column("RX pkt/s", justify="right")
        table.add_column("TX pkt/s", justify="right")
        table.add_column("Errors", justify="right")

        for interface, stat in network_stats.items():
            rx_mb = stat.get("rx_rate", 0) / (1024 * 1024)
            tx_mb = stat.get("tx_rate", 0) / (1024 * 1024)
            rx_pkt = stat.get("rx_packets", 0)
            tx_pkt = stat.get("tx_packets", 0)
            errors = stat.get("rx_errors", 0) + stat.get("tx_errors", 0)

            table.add_row(
                interface,
                f"{rx_mb:.2f}",
                f"{tx_mb:.2f}",
                f"{rx_pkt:.0f}",
                f"{tx_pkt:.0f}",
                f"{errors}",
            )

        if not network_stats:
            table.add_row("No interfaces", "-", "-", "-", "-", "-")

        return Panel(
            table,
            title="[bold]Network I/O[/bold]",
            border_style=self.theme["primary"],
            padding=(0, 1),
        )

    def build_layout(self, stats: Dict[str, Any]) -> Layout:
        """Build the complete UI layout"""
        layout = Layout()

        # Main structure
        layout.split_column(
            Layout(name="header", size=1),
            Layout(name="top", size=8),
            Layout(name="middle", size=6),
            Layout(name="io_tables", size=8),  # Renamed from disk_table
            Layout(name="footer", size=3),
        )

        # Header
        header = Text(
            "DGXTOP - DGX SPARK",
            style=f"bold {self.theme['primary']}",
            justify="center",
        )
        layout["header"].update(header)

        # Top row: CPU | GPU
        layout["top"].split_row(
            Layout(name="cpu"),
            Layout(name="gpu"),
        )
        layout["cpu"].update(self._build_cpu_panel(stats))
        layout["gpu"].update(self._build_gpu_panel(stats))

        # Middle row: Memory | Disk History
        layout["middle"].split_row(
            Layout(name="memory"),
            Layout(name="disk_history"),
        )
        layout["memory"].update(self._build_memory_panel(stats))
        layout["disk_history"].update(self._build_disk_history_panel(stats))

        # I/O tables row: Disk | Network (side by side)
        layout["io_tables"].split_row(
            Layout(name="disk_table"),
            Layout(name="network_table"),
        )
        layout["disk_table"].update(self._build_disk_table(stats))
        layout["network_table"].update(self._build_network_table(stats))

        # Footer with copyright
        footer_text = Text()
        footer_text.append("© 2026 Will 保哥 - DGX SPARK System Monitor", style="dim")
        footer_panel = Panel(
            footer_text,
            border_style=self.theme["primary"],
            padding=(0, 2),
        )
        layout["footer"].update(footer_panel)


        # Footer with copyright
        footer_text = Text()
        footer_text.append("© 2026 Will 保哥 - DGX SPARK System Monitor", style="dim")
        footer_panel = Panel(
            footer_text,
            border_style=self.theme["primary"],
            padding=(0, 2),
        )
        layout["footer"].update(footer_panel)

        return layout

    def get_renderable(self, stats: Dict[str, Any]):
        """Get the renderable layout for Live display"""
        return self.build_layout(stats)
