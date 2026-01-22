"""Main hardware agent client wrapper."""

from typing import Optional

from rich.console import Console

from copilot import CopilotClient, CopilotSession
from copilot.generated.session_events import SessionEvent

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

from .events import handle_event

console = Console()

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
    """

    def __init__(self) -> None:
        """Initialize the Hardware Agent."""
        self.client: Optional[CopilotClient] = None
        self.session: Optional[CopilotSession] = None

    async def initialize(self) -> None:
        """Initialize the Copilot client and create session.

        This method starts the Copilot client and creates a new session
        with all the hardware monitoring tools, custom agents, and
        permission handlers configured.
        """
        console.print("[blue]Initializing Hardware Agent...[/blue]")

        self.client = CopilotClient({"log_level": LOG_LEVEL, "auto_start": True})

        await self.client.start()

        # Create session with all features
        self.session = await self.client.create_session(
            {
                "model": DEFAULT_MODEL,
                "streaming": True,
                # Custom tools
                "tools": [
                    # Shell tools
                    run_foreground_command,
                    run_background_command,
                    # Job management
                    list_background_jobs,
                    get_job_status,
                    stop_background_job,
                    remove_job,
                    # Hardware monitoring
                    get_cpu_stats,
                    get_memory_stats,
                    get_disk_stats,
                    get_network_stats,
                    get_top_processes,
                    # Plotting
                    create_plot,
                    create_multi_series_plot,
                    create_system_dashboard,
                ],
                # Custom agents
                "custom_agents": HARDWARE_AGENTS,
                # Permission handler (hooks)
                "on_permission_request": on_permission_request,
                # System message (custom instructions)
                "system_message": {"mode": "append", "content": SYSTEM_INSTRUCTIONS},
                # Load skills from directory
                "skill_directories": ["./skills"],
            }
        )

        # Set up event handlers
        self._setup_event_handlers()

        console.print("[green]✓ Hardware Agent ready![/green]")

    def _setup_event_handlers(self) -> None:
        """Configure event handlers for streaming and status."""
        if self.session:
            self.session.on(self._handle_event)

    def _handle_event(self, event: SessionEvent) -> None:
        """Process session events.

        Args:
            event: The session event to process.
        """
        handle_event(event)

    async def send(self, prompt: str) -> str:
        """Send a message to the agent.

        Args:
            prompt: The user's message/prompt.

        Returns:
            The message ID of the response.

        Raises:
            RuntimeError: If the agent is not initialized.
        """
        if not self.session:
            raise RuntimeError("Agent not initialized")

        return await self.session.send({"prompt": prompt})

    async def send_and_wait(self, prompt: str) -> Optional[SessionEvent]:
        """Send a message and wait for complete response.

        Args:
            prompt: The user's message/prompt.

        Returns:
            The final assistant message event, or None if none was received.

        Raises:
            RuntimeError: If the agent is not initialized.
        """
        if not self.session:
            raise RuntimeError("Agent not initialized")

        return await self.session.send_and_wait({"prompt": prompt})

    async def shutdown(self) -> None:
        """Clean up resources.

        This method destroys the session and stops the client connection.
        """
        console.print("\n[yellow]Shutting down...[/yellow]")

        if self.session:
            await self.session.destroy()

        if self.client:
            await self.client.stop()

        console.print("[green]Goodbye![/green]")
