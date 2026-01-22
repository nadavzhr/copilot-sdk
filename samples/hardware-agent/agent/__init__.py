"""Hardware Agent - Main agent module."""

from .config import AGENT_NAME, DEFAULT_MODEL

__all__ = ["AGENT_NAME", "DEFAULT_MODEL"]


def get_hardware_agent():
    """Lazy import to avoid circular dependency."""
    from .client import HardwareAgent

    return HardwareAgent
