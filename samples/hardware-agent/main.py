#!/usr/bin/env python3
"""Hardware Agent CLI - Main entry point.

This module provides the main CLI interface for the Hardware Agent,
an AI assistant specialized in system monitoring, diagnostics, and
data visualization powered by the GitHub Copilot SDK.
"""

import asyncio
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from agent.client import HardwareAgent

console = Console()

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

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    finally:
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
