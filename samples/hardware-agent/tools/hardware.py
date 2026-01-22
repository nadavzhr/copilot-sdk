"""Hardware monitoring tools using psutil."""

import psutil
from pydantic import BaseModel, Field

from copilot import define_tool


class MetricParams(BaseModel):
    """Parameters for CPU metrics collection."""

    interval: float = Field(default=1.0, description="Sampling interval in seconds")


class DiskParams(BaseModel):
    """Parameters for disk usage query."""

    path: str = Field(default="/", description="Path to check disk usage")


@define_tool(description="Get current CPU usage percentage and stats")
async def get_cpu_stats(params: MetricParams) -> dict:
    """Get CPU statistics.

    Args:
        params: Parameters containing the sampling interval.

    Returns:
        Dictionary with overall percentage, per-core percentages,
        core count, and frequency information.
    """
    cpu_percent = psutil.cpu_percent(interval=params.interval, percpu=True)
    cpu_freq = psutil.cpu_freq()

    return {
        "overall_percent": sum(cpu_percent) / len(cpu_percent),
        "per_core_percent": cpu_percent,
        "core_count": psutil.cpu_count(),
        "frequency_mhz": cpu_freq.current if cpu_freq else None,
        "frequency_max_mhz": cpu_freq.max if cpu_freq else None,
    }


@define_tool(description="Get memory usage statistics")
async def get_memory_stats() -> dict:
    """Get memory statistics.

    Returns:
        Dictionary with total, available, used memory in GB,
        percentage used, and swap information.
    """
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "percent_used": mem.percent,
        "swap_total_gb": round(swap.total / (1024**3), 2),
        "swap_used_percent": swap.percent,
    }


@define_tool(description="Get disk usage for a specific path")
async def get_disk_stats(params: DiskParams) -> dict:
    """Get disk usage statistics.

    Args:
        params: Parameters containing the path to check.

    Returns:
        Dictionary with disk usage details for the specified path.
    """
    try:
        disk = psutil.disk_usage(params.path)
        return {
            "path": params.path,
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent_used": round(disk.percent, 1),
        }
    except Exception as e:
        return {"error": str(e)}


@define_tool(description="Get network I/O statistics")
async def get_network_stats() -> dict:
    """Get network statistics.

    Returns:
        Dictionary with bytes sent/received, packets sent/received,
        and error counts.
    """
    net = psutil.net_io_counters()

    return {
        "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
        "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2),
        "packets_sent": net.packets_sent,
        "packets_recv": net.packets_recv,
        "errors_in": net.errin,
        "errors_out": net.errout,
    }


@define_tool(description="Get list of running processes with resource usage")
async def get_top_processes() -> dict:
    """Get top processes by CPU and memory.

    Returns:
        Dictionary with top 10 processes by CPU usage and total process count.
    """
    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = proc.info
            if info["cpu_percent"] > 0 or info["memory_percent"] > 0.1:
                processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Sort by CPU usage
    processes.sort(key=lambda x: x["cpu_percent"] or 0, reverse=True)

    return {
        "top_by_cpu": processes[:10],
        "total_processes": len(list(psutil.process_iter())),
    }
