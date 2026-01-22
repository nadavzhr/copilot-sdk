"""Main hardware agent client wrapper."""

import asyncio
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from copilot import CopilotClient, CopilotSession
from copilot.generated.session_events import SessionEvent, SessionEventType

from agent.config import DEFAULT_MODEL, LOG_LEVEL
from agents.definitions import HARDWARE_AGENTS
from hooks.permissions import on_permission_request
from tools import (
    create_multi_series_plot,
    create_plot,
    create_system_dashboard,
    get_cpu_stats,
    get_disk_stats,
    get_job_status,
    get_memory_stats,
    get_network_stats,
    get_top_processes,
    list_background_jobs,
    remove_job,
    run_background_command,
    run_foreground_command,
    stop_background_job,
)

SYSTEM_INSTRUCTIONS = """
<context>
You are a Hardware Agent - an AI assistant specialized in system monitoring,
diagnostics, and data visualization. You help users understand and manage
their system resources.
</context>

<capabilities>
- Execute shell commands (foreground or background)
- Track and manage background jobs
- Monitor CPU, memory, disk, and network
- Generate plots and visualizations from data
- Create system resource dashboards
</capabilities>

<guidelines>
- Always explain what you're about to do before taking action
- For long-running commands, suggest background execution
- When showing metrics, provide context (is this value normal?)
- Create visualizations to make data easier to understand
- Be proactive about identifying potential issues
- Keep responses concise and well-formatted
</guidelines>
"""


class HardwareAgent:
    """Hardware monitoring and management agent.

    This class provides a high-level interface for interacting with the
    Copilot SDK to perform hardware monitoring, system diagnostics, and
    data visualization tasks.

    Attributes:
        client: The CopilotClient instance for managing the connection.
        session: The active CopilotSession for the conversation.
        console: Rich console for output.
    """

    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize the Hardware Agent.
        
        Args:
            console: Optional Rich console for output. Creates a new one if not provided.
        """
        self.client: Optional[CopilotClient] = None
        self.session: Optional[CopilotSession] = None
        self.console = console or Console()
        self._current_spinner_text = ""
        self._output_buffer = ""
        self._tool_count = 0

    async def initialize(self) -> None:
        """Initialize the Copilot client and create session."""
        with self.console.status("[bold blue]Connecting to GitHub Copilot...", spinner="dots"):
            self.client = CopilotClient({"log_level": LOG_LEVEL, "auto_start": True})
            await self.client.start()

        with self.console.status("[bold blue]Creating AI session...", spinner="dots"):
            self.session = await self.client.create_session(
                {
                    "model": DEFAULT_MODEL,
                    "streaming": True,
                    "tools": [
                        run_foreground_command,
                        run_background_command,
                        list_background_jobs,
                        get_job_status,
                        stop_background_job,
                        remove_job,
                        get_cpu_stats,
                        get_memory_stats,
                        get_disk_stats,
                        get_network_stats,
                        get_top_processes,
                        create_plot,
                        create_multi_series_plot,
                        create_system_dashboard,
                    ],
                    "custom_agents": HARDWARE_AGENTS,
                    "on_permission_request": on_permission_request,
                    "system_message": {"mode": "append", "content": SYSTEM_INSTRUCTIONS},
                    "skill_directories": ["./skills"],
                }
            )

        self.console.print("[green]✓ Hardware Agent ready![/green]")

    async def generate(self, prompt: str, timeout: float = 120.0) -> Optional[str]:
        """Send a message and wait for the complete response.

        Args:
            prompt: The user's message/prompt.
            timeout: Maximum time to wait for response (default: 120 seconds).

        Returns:
            The complete response text, or None if an error occurred.

        Raises:
            RuntimeError: If the agent is not initialized.
        """
        if not self.session:
            raise RuntimeError("Agent not initialized")

        self._output_buffer = ""
        self._tool_count = 0
        self._current_spinner_text = ""
        idle_event = asyncio.Event()
        error_message: Optional[str] = None

        def event_handler(event: SessionEvent) -> None:
            nonlocal error_message

            if event.type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
                delta = getattr(event.data, "delta_content", "")
                if delta:
                    self._output_buffer += delta

            elif event.type == SessionEventType.ASSISTANT_MESSAGE:
                # Final message - get full content
                content = getattr(event.data, "content", "")
                if content:
                    self._output_buffer = content

            elif event.type == SessionEventType.TOOL_EXECUTION_START:
                self._tool_count += 1
                tool_name = getattr(event.data, "tool_name", "unknown")
                friendly_name = self._get_tool_friendly_name(tool_name)
                self._current_spinner_text = f"{friendly_name['emoji']} {friendly_name['action']}"

            elif event.type == SessionEventType.TOOL_EXECUTION_COMPLETE:
                self._current_spinner_text = ""  # Clear after tool completes

            elif event.type == SessionEventType.SESSION_IDLE:
                idle_event.set()

            elif event.type == SessionEventType.SESSION_ERROR:
                error_message = getattr(event.data, "message", "Unknown error")
                idle_event.set()

        # Subscribe to events
        unsubscribe = self.session.on(event_handler)

        try:
            # Show spinner while waiting
            with self.console.status(
                "[bold cyan]🤔 Thinking...", spinner="dots"
            ) as status:
                # Send the prompt
                await self.session.send({"prompt": prompt})

                # Track elapsed time for timeout
                import time
                start_time = time.monotonic()

                # Wait for completion with periodic status updates
                while not idle_event.is_set():
                    # Check for timeout
                    elapsed = time.monotonic() - start_time
                    if elapsed >= timeout:
                        self.console.print(f"[yellow]⚠️ Request timed out after {timeout}s[/yellow]")
                        return None

                    # Update spinner text if tools are running
                    if self._current_spinner_text:
                        status.update(f"[bold cyan]{self._current_spinner_text}")
                    elif self._output_buffer:
                        lines = len(self._output_buffer.split("\n"))
                        status.update(f"[bold cyan]✨ Generating response... ({lines} lines)")

                    # Wait for idle event with short timeout for UI updates
                    try:
                        await asyncio.wait_for(idle_event.wait(), timeout=0.5)
                    except asyncio.TimeoutError:
                        continue  # Keep waiting, check timeout on next iteration

            if error_message:
                self.console.print(f"[red]❌ Error: {error_message}[/red]")
                return None

            return self._output_buffer.strip() if self._output_buffer else None

        finally:
            unsubscribe()

    def _get_tool_friendly_name(self, tool_name: str) -> dict:
        """Get user-friendly name and emoji for a tool."""
        tool_map = {
            "get_cpu_stats": {"emoji": "📊", "action": "Measuring CPU usage..."},
            "get_memory_stats": {"emoji": "🧠", "action": "Checking memory..."},
            "get_disk_stats": {"emoji": "💾", "action": "Analyzing disk usage..."},
            "get_network_stats": {"emoji": "🌐", "action": "Checking network..."},
            "get_top_processes": {"emoji": "📋", "action": "Listing processes..."},
            "run_foreground_command": {"emoji": "⚡", "action": "Running command..."},
            "run_background_command": {"emoji": "🔄", "action": "Starting background job..."},
            "list_background_jobs": {"emoji": "📋", "action": "Listing jobs..."},
            "get_job_status": {"emoji": "🔍", "action": "Checking job status..."},
            "stop_background_job": {"emoji": "🛑", "action": "Stopping job..."},
            "remove_job": {"emoji": "🗑️", "action": "Removing job..."},
            "create_plot": {"emoji": "📈", "action": "Creating chart..."},
            "create_multi_series_plot": {"emoji": "📈", "action": "Creating multi-series chart..."},
            "create_system_dashboard": {"emoji": "📊", "action": "Generating dashboard..."},
        }
        return tool_map.get(tool_name, {"emoji": "⚙️", "action": f"Running {tool_name}..."})

    async def shutdown(self) -> None:
        """Clean up resources."""
        self.console.print("\n[yellow]Shutting down...[/yellow]")

        if self.session:
            try:
                await self.session.destroy()
            except Exception:
                pass  # Ignore cleanup errors

        if self.client:
            try:
                await self.client.stop()
            except Exception:
                pass  # Ignore cleanup errors

        self.console.print("[green]Goodbye![/green]")
