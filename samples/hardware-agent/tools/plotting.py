"""Data visualization and plotting tools."""

import json
import os
from datetime import datetime
from typing import Literal

import matplotlib
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field

from copilot import define_tool

from agent.config import DEFAULT_PLOT_DIR, PLOT_DPI

# Use non-interactive backend for server-side rendering
matplotlib.use("Agg")


class PlotDataParams(BaseModel):
    """Parameters for creating a single plot."""

    data: str = Field(description="JSON string of data points, e.g., {'x': [1,2,3], 'y': [4,5,6]}")
    title: str = Field(description="Title of the plot")
    x_label: str = Field(default="X", description="Label for X axis")
    y_label: str = Field(default="Y", description="Label for Y axis")
    plot_type: Literal["line", "bar", "scatter", "pie"] = Field(default="line")
    filename: str = Field(description="Output filename (without extension)")


class MultiSeriesPlotParams(BaseModel):
    """Parameters for creating a multi-series plot."""

    data: str = Field(description="JSON with multiple series: {'series1': {'x':[], 'y':[]}, ...}")
    title: str = Field(description="Title of the plot")
    x_label: str = Field(default="X", description="Label for X axis")
    y_label: str = Field(default="Y", description="Label for Y axis")
    filename: str = Field(description="Output filename (without extension)")


@define_tool(description="Generate a plot/graph from data and save to filesystem")
async def create_plot(params: PlotDataParams) -> dict:
    """Create a plot from provided data.

    Args:
        params: Parameters containing plot data and configuration.

    Returns:
        Dictionary with success status, filepath, and message, or error details.
    """
    os.makedirs(DEFAULT_PLOT_DIR, exist_ok=True)

    try:
        data = json.loads(params.data)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON data: {e}"}

    fig, ax = plt.subplots(figsize=(10, 6))

    try:
        if params.plot_type == "line":
            ax.plot(data.get("x", []), data.get("y", []), marker="o")
        elif params.plot_type == "bar":
            ax.bar(data.get("x", []), data.get("y", []))
        elif params.plot_type == "scatter":
            ax.scatter(data.get("x", []), data.get("y", []))
        elif params.plot_type == "pie":
            ax.pie(
                data.get("values", []),
                labels=data.get("labels", []),
                autopct="%1.1f%%",
            )

        ax.set_title(params.title)
        if params.plot_type != "pie":
            ax.set_xlabel(params.x_label)
            ax.set_ylabel(params.y_label)
            ax.grid(True, alpha=0.3)

        filepath = os.path.join(DEFAULT_PLOT_DIR, f"{params.filename}.png")
        plt.savefig(filepath, dpi=PLOT_DPI, bbox_inches="tight")
        plt.close(fig)

        return {
            "success": True,
            "filepath": os.path.abspath(filepath),
            "message": f"Plot saved to {filepath}",
        }
    except Exception as e:
        plt.close(fig)
        return {"error": str(e)}


@define_tool(description="Generate a multi-series line plot from data")
async def create_multi_series_plot(params: MultiSeriesPlotParams) -> dict:
    """Create a multi-series plot from provided data.

    Args:
        params: Parameters containing multi-series plot data and configuration.

    Returns:
        Dictionary with success status, filepath, and message, or error details.
    """
    os.makedirs(DEFAULT_PLOT_DIR, exist_ok=True)

    try:
        data = json.loads(params.data)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON data: {e}"}

    fig, ax = plt.subplots(figsize=(12, 6))

    try:
        for series_name, series_data in data.items():
            ax.plot(
                series_data.get("x", []),
                series_data.get("y", []),
                marker="o",
                label=series_name,
            )

        ax.set_title(params.title)
        ax.set_xlabel(params.x_label)
        ax.set_ylabel(params.y_label)
        ax.legend()
        ax.grid(True, alpha=0.3)

        filepath = os.path.join(DEFAULT_PLOT_DIR, f"{params.filename}.png")
        plt.savefig(filepath, dpi=PLOT_DPI, bbox_inches="tight")
        plt.close(fig)

        return {
            "success": True,
            "filepath": os.path.abspath(filepath),
            "message": f"Multi-series plot saved to {filepath}",
        }
    except Exception as e:
        plt.close(fig)
        return {"error": str(e)}


@define_tool(description="Generate a system resource dashboard with multiple charts")
async def create_system_dashboard() -> dict:
    """Create a comprehensive system dashboard with CPU, memory, disk, and network charts.

    Returns:
        Dictionary with success status, filepath, and message, or error details.
    """
    import psutil

    os.makedirs(DEFAULT_PLOT_DIR, exist_ok=True)

    try:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle("System Resource Dashboard", fontsize=14, fontweight="bold")

        # CPU Usage per core
        cpu_percent = psutil.cpu_percent(interval=0.5, percpu=True)
        axes[0, 0].bar(
            [f"Core {i}" for i in range(len(cpu_percent))],
            cpu_percent,
            color="steelblue",
        )
        axes[0, 0].set_title("CPU Usage by Core")
        axes[0, 0].set_ylabel("Usage (%)")
        axes[0, 0].set_ylim(0, 100)

        # Memory Usage
        mem = psutil.virtual_memory()
        mem_labels = ["Used", "Available"]
        mem_values = [mem.used / (1024**3), mem.available / (1024**3)]
        colors = ["#ff6b6b", "#4ecdc4"]
        axes[0, 1].pie(
            mem_values,
            labels=mem_labels,
            autopct="%1.1f%%",
            colors=colors,
            startangle=90,
        )
        axes[0, 1].set_title(f"Memory Usage (Total: {mem.total / (1024**3):.1f} GB)")

        # Disk Usage
        disk = psutil.disk_usage("/")
        disk_labels = ["Used", "Free"]
        disk_values = [disk.used / (1024**3), disk.free / (1024**3)]
        axes[1, 0].pie(
            disk_values,
            labels=disk_labels,
            autopct="%1.1f%%",
            colors=["#ffa726", "#66bb6a"],
            startangle=90,
        )
        axes[1, 0].set_title(f"Disk Usage (Total: {disk.total / (1024**3):.1f} GB)")

        # Network I/O
        net = psutil.net_io_counters()
        net_labels = ["Sent (MB)", "Received (MB)"]
        net_values = [net.bytes_sent / (1024**2), net.bytes_recv / (1024**2)]
        bars = axes[1, 1].bar(net_labels, net_values, color=["#7e57c2", "#42a5f5"])
        axes[1, 1].set_title("Network I/O")
        axes[1, 1].set_ylabel("Megabytes")

        # Add value labels on bars
        for bar, val in zip(bars, net_values):
            axes[1, 1].text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{val:.1f}",
                ha="center",
                va="bottom",
            )

        plt.tight_layout()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(DEFAULT_PLOT_DIR, f"dashboard_{timestamp}.png")
        plt.savefig(filepath, dpi=PLOT_DPI, bbox_inches="tight")
        plt.close(fig)

        return {
            "success": True,
            "filepath": os.path.abspath(filepath),
            "message": f"System dashboard saved to {filepath}",
        }
    except Exception as e:
        plt.close("all")
        return {"error": str(e)}
