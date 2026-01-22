#!/usr/bin/env python3
"""Hardware Agent CLI - Main entry point.

This module provides the main CLI interface for the Hardware Agent,
an AI assistant specialized in system monitoring, diagnostics, and
data visualization powered by the GitHub Copilot SDK.
"""

import asyncio
import shutil
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

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
[bold]Available Commands:[/bold]
  [cyan]exit, quit[/cyan]     - Exit the agent
  [cyan]help[/cyan]           - Show this help message
  [cyan]jobs[/cyan]           - List background jobs
  [cyan]dashboard[/cyan]      - Generate system dashboard

[bold]Example Prompts:[/bold]
  • "Show me current CPU and memory usage"
  • "Run htop in the background and track it"
  • "Create a plot of the top 5 processes by memory"
  • "Monitor disk usage on /home"
  • "What background jobs are running?"
"""


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

    agent = HardwareAgent()

    try:
        await agent.initialize()
        console.print(Panel(HELP_TEXT, title="Quick Start", border_style="dim"))
        console.print()

        while True:
            try:
                user_input = Prompt.ask("[bold green]You[/bold green]")

                if not user_input.strip():
                    continue

                lower_input = user_input.lower().strip()

                # Built-in commands
                if lower_input in ("exit", "quit"):
                    break
                elif lower_input == "help":
                    console.print(Panel(HELP_TEXT, title="Help", border_style="dim"))
                    continue
                elif lower_input == "jobs":
                    user_input = "List all background jobs and their status"
                elif lower_input == "dashboard":
                    user_input = "Generate a system resource dashboard and save it"

                console.print()
                console.print("[bold cyan]Agent:[/bold cyan] ", end="")

                await agent.send(user_input)

                console.print()

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
                continue

    except FileNotFoundError as e:
        # Handle case where CLI path is set but file doesn't exist
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
        # Check for common Windows error when CLI not found
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
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
