"""Configuration constants for the hardware agent."""

from typing import Literal

# Agent settings
AGENT_NAME: str = "Hardware Agent"
DEFAULT_MODEL: Literal["gpt-5", "claude-sonnet-4", "claude-sonnet-4.5", "claude-haiku-4.5"] = (
    "claude-sonnet-4"
)
LOG_LEVEL: Literal["none", "error", "warning", "info", "debug", "all"] = "info"

# Job registry settings
JOB_REGISTRY_FILE: str = ".job_registry.json"
MAX_BACKGROUND_JOBS: int = 10

# Plot settings
DEFAULT_PLOT_DIR: str = "./plots"
PLOT_DPI: int = 150
