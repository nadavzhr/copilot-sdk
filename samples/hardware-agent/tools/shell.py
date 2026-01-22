"""Shell command execution tools - foreground and background."""

import subprocess

from pydantic import BaseModel, Field

from copilot import ToolInvocation, define_tool

from registry.job_registry import JobRegistry


class ForegroundCommandParams(BaseModel):
    """Parameters for running a foreground shell command."""

    command: str = Field(description="Shell command to execute")
    timeout: int = Field(default=30, description="Timeout in seconds")


class BackgroundCommandParams(BaseModel):
    """Parameters for running a background shell command."""

    command: str = Field(description="Shell command to run in background")
    job_name: str = Field(description="Friendly name for the job")


@define_tool(description="Execute a shell command in the foreground and return output")
async def run_foreground_command(params: ForegroundCommandParams) -> dict:
    """Run a command and wait for completion.

    Args:
        params: Command execution parameters.

    Returns:
        Dictionary containing stdout, stderr, return code, and success status.
    """
    try:
        result = subprocess.run(
            params.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=params.timeout,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {params.timeout}s"}
    except Exception as e:
        return {"error": str(e)}


@define_tool(description="Start a shell command in the background and track it")
async def run_background_command(
    params: BackgroundCommandParams, invocation: ToolInvocation
) -> dict:
    """Start a background process and register it.

    Args:
        params: Background command parameters.
        invocation: Tool invocation context with session info.

    Returns:
        Dictionary containing job_id, pid, name, status, and confirmation message.
    """
    registry = JobRegistry()

    process = subprocess.Popen(
        params.command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )

    job_id = registry.register_job(
        pid=process.pid,
        name=params.job_name,
        command=params.command,
        session_id=invocation["session_id"],
    )

    return {
        "job_id": job_id,
        "pid": process.pid,
        "name": params.job_name,
        "status": "running",
        "message": f"Background job '{params.job_name}' started with PID {process.pid}",
    }
