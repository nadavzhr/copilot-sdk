"""Custom tools for the Hardware Agent."""

from .hardware import (
    get_cpu_stats,
    get_disk_stats,
    get_memory_stats,
    get_network_stats,
    get_top_processes,
)
from .jobs import (
    get_job_status,
    list_background_jobs,
    remove_job,
    stop_background_job,
)
from .plotting import (
    create_multi_series_plot,
    create_plot,
    create_system_dashboard,
)
from .shell import run_background_command, run_foreground_command

__all__ = [
    # Shell tools
    "run_foreground_command",
    "run_background_command",
    # Job management tools
    "list_background_jobs",
    "get_job_status",
    "stop_background_job",
    "remove_job",
    # Hardware monitoring tools
    "get_cpu_stats",
    "get_memory_stats",
    "get_disk_stats",
    "get_network_stats",
    "get_top_processes",
    # Plotting tools
    "create_plot",
    "create_multi_series_plot",
    "create_system_dashboard",
]
