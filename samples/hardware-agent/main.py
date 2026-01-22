#!/usr/bin/env python3
"""Hardware Agent CLI - Main entry point.

This module provides the main CLI interface for the Hardware Agent,
an AI assistant specialized in system monitoring, diagnostics, and
data visualization powered by the GitHub Copilot SDK.
"""

import asyncio
import shutil
import sys
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.spinner import Spinner
from rich.text import Text

from agent.client import HardwareAgent

console = Console()


def check_copilot_cli() -> bool:
    """Check if the Copilot CLI is installed and available.

    Returns:
        True if the CLI is found, False otherwise.
    """
    return shutil.which("copilot") is not None


BANNER = """
╔═══════════════════════════════════════════════════════════╗
║               🖥️  HARDWARE AGENT CLI  🖥️                  ║
║                                                           ║
║  System monitoring, diagnostics, and visualization        ║
║  Powered by GitHub Copilot SDK                            ║
╚═══════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
[bold]Slash Commands:[/bold]
  [cyan]/cpu[/cyan]           - Show CPU statistics
  [cyan]/memory[/cyan]        - Show memory usage
  [cyan]/disk[/cyan]          - Show disk usage
  [cyan]/network[/cyan]       - Show network stats
  [cyan]/top[/cyan]           - Show top processes
  [cyan]/dashboard[/cyan]     - Generate system dashboard
  [cyan]/jobs[/cyan]          - List background jobs
  [cyan]/help[/cyan]          - Show this help message
  [cyan]/clear[/cyan]         - Clear the screen
  [cyan]/quit[/cyan]          - Exit the agent

[bold]Or just ask naturally:[/bold]
  • "Show me current CPU and memory usage"
  • "Run a stress test in the background"
  • "Create a plot of the top processes by memory"
  • "What's using the most disk space?"
"""

# Map slash commands to prompts
SLASH_COMMANDS = {
    "/cpu": "Get current CPU statistics and explain if the values are normal",
    "/memory": "Get current memory usage statistics and explain the values",
    "/disk": "Get disk usage for the root filesystem and warn if it's getting full",
    "/network": "Get network I/O statistics",
    "/dashboard": "Create a comprehensive system resource dashboard and save it to a file",
    "/jobs": "List all background jobs and their current status",
    "/top": "Show the top processes by CPU and memory usage",
}


async def main() -> None:
    """Main entry point for the Hardware Agent CLI."""
    console.print(BANNER, style="bold blue")

    # Check for Copilot CLI before attempting to start
    if not check_copilot_cli():
        console.print(
            Panel(
                "[bold red]GitHub Copilot CLI not found![/bold red]\n\n"
                "The Hardware Agent requires the GitHub Copilot CLI to be installed.\n\n"
                "[bold]To install:[/bold]\n"
                "  1. Install GitHub Copilot CLI from: "
                "[link]https://docs.github.com/en/copilot/github-copilot-in-the-cli[/link]\n"
                "  2. Ensure 'copilot' is in your system PATH\n"
                "  3. Authenticate with: [cyan]copilot auth login[/cyan]\n\n"
                "[dim]Alternatively, set COPILOT_CLI_PATH environment variable "
                "to the full path of the CLI executable.[/dim]",
                title="⚠️  Missing Dependency",
                border_style="red",
            )
        )
        sys.exit(1)

    agent: Optional[HardwareAgent] = None

    try:
        agent = HardwareAgent(console)
        await agent.initialize()

        console.print(Panel(HELP_TEXT, title="Quick Start", border_style="dim"))
        console.print()

        while True:
            try:
                user_input = Prompt.ask("[bold green]You[/bold green]")

                if not user_input.strip():
                    continue

                input_lower = user_input.lower().strip()

                # Handle slash commands
                if input_lower in ("/quit", "/exit"):
                    break
                elif input_lower == "/help":
                    console.print(Panel(HELP_TEXT, title="Help", border_style="dim"))
                    continue
                elif input_lower == "/clear":
                    console.clear()
                    console.print(BANNER, style="bold blue")
                    continue
                elif input_lower in SLASH_COMMANDS:
                    user_input = SLASH_COMMANDS[input_lower]

                console.print()

                # Send and wait for complete response
                response = await agent.generate(user_input)

                if response:
                    console.print()
                    console.print(Panel(response, title="[bold cyan]Agent[/bold cyan]", border_style="cyan"))
                console.print()

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type /quit to exit.[/yellow]")
                continue
            except asyncio.CancelledError:
                # Handle task cancellation gracefully (can happen during permission prompts)
                console.print("\n[yellow]Operation cancelled. Try again.[/yellow]")
                continue

    except FileNotFoundError as e:
        console.print(
            Panel(
                f"[bold red]Could not start Copilot CLI:[/bold red]\n\n"
                f"{e}\n\n"
                "[bold]Please ensure:[/bold]\n"
                "  1. GitHub Copilot CLI is installed\n"
                "  2. The 'copilot' command is in your PATH\n"
                "  3. You are authenticated with: [cyan]copilot auth login[/cyan]",
                title="⚠️  CLI Error",
                border_style="red",
            )
        )
        sys.exit(1)

    except Exception as e:
        error_msg = str(e)
        if "WinError 2" in error_msg or "cannot find the file" in error_msg.lower():
            console.print(
                Panel(
                    "[bold red]GitHub Copilot CLI not found![/bold red]\n\n"
                    "The 'copilot' command could not be executed.\n\n"
                    "[bold]Please ensure:[/bold]\n"
                    "  1. GitHub Copilot CLI is installed\n"
                    "  2. The 'copilot' command is in your PATH\n"
                    "  3. You are authenticated with: [cyan]copilot auth login[/cyan]\n\n"
                    "[dim]On Windows, you may need to restart your terminal "
                    "after installation.[/dim]",
                    title="⚠️  CLI Not Found",
                    border_style="red",
                )
            )
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    finally:
        if agent:
            await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
