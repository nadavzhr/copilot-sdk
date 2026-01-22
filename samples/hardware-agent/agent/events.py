"""Event handlers for the Hardware Agent."""

from rich.console import Console

from copilot.generated.session_events import SessionEvent, SessionEventType

console = Console()


def handle_event(event: SessionEvent) -> None:
    """Process session events and display them appropriately.

    This handler processes various event types from the Copilot session
    and displays them in a user-friendly format using rich console.

    Args:
        event: The session event to process.
    """
    event_type = event.type

    if event_type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
        # Stream response chunks
        data = event.data
        delta = getattr(data, "delta_content", "")
        if delta:
            console.print(delta, end="")

    elif event_type == SessionEventType.TOOL_EXECUTION_START:
        # Show when a tool starts executing
        data = event.data
        tool_name = getattr(data, "tool_name", "unknown")
        console.print(f"\n[dim]🔧 Running: {tool_name}...[/dim]")

    elif event_type == SessionEventType.TOOL_EXECUTION_COMPLETE:
        # Show tool completion
        console.print("[dim]✓[/dim]", end=" ")

    elif event_type == SessionEventType.SUBAGENT_SELECTED:
        # Show when a sub-agent is selected
        data = event.data
        agent_name = getattr(data, "agent_display_name", "unknown")
        console.print(f"\n[magenta]🤖 Agent: {agent_name}[/magenta]")

    elif event_type == SessionEventType.SESSION_IDLE:
        # New line after response completes
        console.print()

    elif event_type == SessionEventType.SESSION_ERROR:
        # Display errors
        data = event.data
        message = getattr(data, "message", "Unknown error")
        console.print(f"\n[red]❌ Error: {message}[/red]")

    elif event_type == SessionEventType.ASSISTANT_REASONING_DELTA:
        # Show reasoning (if available)
        data = event.data
        delta = getattr(data, "delta_content", "")
        if delta:
            console.print(f"[dim italic]{delta}[/dim italic]", end="")
