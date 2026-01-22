"""Permission request handlers for sensitive operations."""

from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from copilot import PermissionRequest, PermissionRequestResult

console = Console()

# Commands that are always safe (read-only operations)
SAFE_COMMANDS: List[str] = [
    "ls",
    "pwd",
    "whoami",
    "date",
    "cat",
    "head",
    "tail",
    "echo",
    "ps",
    "top",
    "df",
    "free",
    "uname",
    "hostname",
    "uptime",
    "which",
    "whereis",
    "env",
    "printenv",
]

# Commands that require explicit approval due to potential danger
DANGEROUS_COMMANDS: List[str] = [
    "rm",
    "dd",
    "mkfs",
    "chmod",
    "chown",
    "kill",
    "pkill",
    "shutdown",
    "reboot",
    "format",
    "fdisk",
    "parted",
]


def on_permission_request(
    request: PermissionRequest, invocation: Dict[str, Any]
) -> PermissionRequestResult:
    """Handle permission requests from the agent.

    This function is called when the agent needs permission to perform
    certain actions such as running shell commands or writing files.

    Args:
        request: The permission request containing the operation details.
        invocation: Context dictionary containing session information.

    Returns:
        PermissionRequestResult indicating whether the operation is approved or denied.
    """
    kind = request.get("kind", "unknown")

    console.print(
        Panel(
            f"[yellow]Permission Request[/yellow]\n"
            f"Type: [bold]{kind}[/bold]\n"
            f"Session: {invocation.get('session_id', 'unknown')[:8]}...",
            title="⚠️  Agent Requesting Permission",
        )
    )

    # Handle shell commands
    if kind == "shell":
        command = str(request.get("command", ""))
        console.print(f"Command: [cyan]{command}[/cyan]")

        # Check for safe commands
        cmd_base = command.split()[0] if command else ""
        if cmd_base in SAFE_COMMANDS:
            console.print("[green]Auto-approved (safe command)[/green]")
            return {"kind": "approved"}

        # Check for dangerous commands
        if any(dc in command for dc in DANGEROUS_COMMANDS):
            console.print("[red]⚠️  This is a potentially dangerous command![/red]")

        # Ask user
        if Confirm.ask("Allow this command?"):
            return {"kind": "approved"}
        else:
            return {"kind": "denied-interactively-by-user"}

    # Handle file writes
    elif kind == "write":
        path = request.get("path", "unknown")
        console.print(f"File: [cyan]{path}[/cyan]")

        if Confirm.ask("Allow file write?"):
            return {"kind": "approved"}
        else:
            return {"kind": "denied-interactively-by-user"}

    # Handle file reads
    elif kind == "read":
        path = request.get("path", "unknown")
        console.print(f"File: [cyan]{path}[/cyan]")

        # Auto-approve read operations
        console.print("[green]Auto-approved (read operation)[/green]")
        return {"kind": "approved"}

    # Default: ask user for unknown operation types
    else:
        if Confirm.ask(f"Allow {kind} operation?"):
            return {"kind": "approved"}
        else:
            return {"kind": "denied-interactively-by-user"}
