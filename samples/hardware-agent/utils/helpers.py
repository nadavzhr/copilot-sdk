"""Utility helper functions for the Hardware Agent."""


def format_bytes(bytes_value: int) -> str:
    """Format a byte value into human-readable form.

    Args:
        bytes_value: Number of bytes to format.

    Returns:
        Human-readable string (e.g., "1.23 GB", "456 MB").
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(bytes_value) < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_uptime(seconds: float) -> str:
    """Format seconds into a human-readable uptime string.

    Args:
        seconds: Number of seconds of uptime.

    Returns:
        Human-readable string (e.g., "2 days, 3 hours, 15 minutes").
    """
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if not parts:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")

    return ", ".join(parts)


def truncate_string(text: str, max_length: int = 50) -> str:
    """Truncate a string to a maximum length with ellipsis.

    Args:
        text: The string to truncate.
        max_length: Maximum allowed length (default: 50).

    Returns:
        Truncated string with "..." if it exceeded max_length.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
