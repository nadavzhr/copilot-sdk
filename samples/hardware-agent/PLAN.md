# Hardware-Oriented Agentic CLI Tool - Implementation Plan

## 🎯 Project Overview

A proof-of-concept Python CLI tool that demonstrates all modern agentic workflow features of the GitHub Copilot SDK. The agent specializes in hardware monitoring, system diagnostics, and data visualization.

### Key Capabilities
- **Shell Command Execution**: Run commands in foreground or background
- **Background Job Registry**: Track and manage long-running processes
- **Data Visualization**: Generate graphs/plots from system metrics
- **Hardware Monitoring**: CPU, memory, disk, network statistics

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Hardware Agent CLI                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Custom    │  │   Custom    │  │   Permission        │  │
│  │   Tools     │  │   Agents    │  │   Handlers          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    MCP      │  │   Skills    │  │   Background Job    │  │
│  │   Servers   │  │  Directory  │  │   Registry          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                   Copilot SDK (Python)                       │
│                         ↓ JSON-RPC                           │
│                   Copilot CLI Server                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
samples/hardware-agent/
├── PLAN.md                    # This file
├── README.md                  # Usage instructions
├── requirements.txt           # Python dependencies
├── main.py                    # CLI entry point
├── agent/
│   ├── __init__.py
│   ├── client.py              # Main agent client wrapper
│   ├── config.py              # Configuration and constants
│   └── events.py              # Event handlers
├── tools/
│   ├── __init__.py
│   ├── shell.py               # Shell command execution tools
│   ├── jobs.py                # Background job management tools
│   ├── hardware.py            # Hardware monitoring tools
│   └── plotting.py            # Data visualization tools
├── agents/
│   ├── __init__.py
│   ├── sysadmin.py            # System administrator agent
│   ├── analyst.py             # Data analyst agent
│   └── definitions.py         # Agent configurations
├── hooks/
│   ├── __init__.py
│   └── permissions.py         # Permission request handlers
├── skills/
│   └── hardware-expert/
│       └── SKILL.md           # Hardware domain knowledge
├── registry/
│   ├── __init__.py
│   └── job_registry.py        # Background job tracking
└── utils/
    ├── __init__.py
    └── helpers.py             # Utility functions
```

---

## 🔧 Feature Implementation Details

### Phase 1: Core Setup & Dependencies

**File: `requirements.txt`**
```
github-copilot-sdk
pydantic>=2.0
matplotlib
psutil
rich
```

**File: `agent/config.py`**
```python
"""Configuration constants for the hardware agent."""

AGENT_NAME = "Hardware Agent"
DEFAULT_MODEL = "gpt-4.1"
LOG_LEVEL = "info"

# Job registry settings
JOB_REGISTRY_FILE = ".job_registry.json"
MAX_BACKGROUND_JOBS = 10

# Plot settings
DEFAULT_PLOT_DIR = "./plots"
PLOT_DPI = 150
```

---

### Phase 2: Custom Tools Implementation

#### 2.1 Shell Command Execution Tool

**File: `tools/shell.py`**
```python
"""Shell command execution tools - foreground and background."""

import subprocess
import asyncio
from pydantic import BaseModel, Field
from copilot import define_tool, ToolInvocation

from registry.job_registry import JobRegistry

class ForegroundCommandParams(BaseModel):
    command: str = Field(description="Shell command to execute")
    timeout: int = Field(default=30, description="Timeout in seconds")

class BackgroundCommandParams(BaseModel):
    command: str = Field(description="Shell command to run in background")
    job_name: str = Field(description="Friendly name for the job")

@define_tool(description="Execute a shell command in the foreground and return output")
async def run_foreground_command(params: ForegroundCommandParams) -> dict:
    """Run a command and wait for completion."""
    try:
        result = subprocess.run(
            params.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=params.timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {params.timeout}s"}
    except Exception as e:
        return {"error": str(e)}

@define_tool(description="Start a shell command in the background and track it")
async def run_background_command(
    params: BackgroundCommandParams,
    invocation: ToolInvocation
) -> dict:
    """Start a background process and register it."""
    registry = JobRegistry()
    
    process = subprocess.Popen(
        params.command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True
    )
    
    job_id = registry.register_job(
        pid=process.pid,
        name=params.job_name,
        command=params.command,
        session_id=invocation["session_id"]
    )
    
    return {
        "job_id": job_id,
        "pid": process.pid,
        "name": params.job_name,
        "status": "running",
        "message": f"Background job '{params.job_name}' started with PID {process.pid}"
    }
```

#### 2.2 Background Job Management Tools

**File: `tools/jobs.py`**
```python
"""Background job management tools."""

import os
import signal
from pydantic import BaseModel, Field
from copilot import define_tool

from registry.job_registry import JobRegistry

class JobIdParams(BaseModel):
    job_id: str = Field(description="The job ID to operate on")

@define_tool(description="List all background jobs and their status")
async def list_background_jobs() -> dict:
    """Get all registered background jobs."""
    registry = JobRegistry()
    jobs = registry.list_jobs()
    
    # Update status for each job
    for job in jobs:
        job["is_running"] = registry.is_job_running(job["pid"])
    
    return {
        "jobs": jobs,
        "total": len(jobs),
        "running": sum(1 for j in jobs if j["is_running"])
    }

@define_tool(description="Get detailed status of a specific background job")
async def get_job_status(params: JobIdParams) -> dict:
    """Get status of a specific job."""
    registry = JobRegistry()
    job = registry.get_job(params.job_id)
    
    if not job:
        return {"error": f"Job {params.job_id} not found"}
    
    job["is_running"] = registry.is_job_running(job["pid"])
    return job

@define_tool(description="Stop/kill a background job by its ID")
async def stop_background_job(params: JobIdParams) -> dict:
    """Stop a running background job."""
    registry = JobRegistry()
    job = registry.get_job(params.job_id)
    
    if not job:
        return {"error": f"Job {params.job_id} not found"}
    
    try:
        os.kill(job["pid"], signal.SIGTERM)
        registry.update_job_status(params.job_id, "stopped")
        return {
            "success": True,
            "message": f"Job {params.job_id} (PID {job['pid']}) stopped"
        }
    except ProcessLookupError:
        registry.update_job_status(params.job_id, "not_found")
        return {"error": "Process not found - may have already exited"}
    except Exception as e:
        return {"error": str(e)}

@define_tool(description="Remove a job from the registry (cleanup)")
async def remove_job(params: JobIdParams) -> dict:
    """Remove a job from the registry."""
    registry = JobRegistry()
    success = registry.remove_job(params.job_id)
    return {
        "success": success,
        "message": f"Job {params.job_id} removed" if success else "Job not found"
    }
```

#### 2.3 Hardware Monitoring Tools

**File: `tools/hardware.py`**
```python
"""Hardware monitoring tools using psutil."""

import psutil
from pydantic import BaseModel, Field
from copilot import define_tool
from typing import Literal

class MetricParams(BaseModel):
    interval: float = Field(default=1.0, description="Sampling interval in seconds")

class DiskParams(BaseModel):
    path: str = Field(default="/", description="Path to check disk usage")

@define_tool(description="Get current CPU usage percentage and stats")
async def get_cpu_stats(params: MetricParams) -> dict:
    """Get CPU statistics."""
    cpu_percent = psutil.cpu_percent(interval=params.interval, percpu=True)
    cpu_freq = psutil.cpu_freq()
    
    return {
        "overall_percent": sum(cpu_percent) / len(cpu_percent),
        "per_core_percent": cpu_percent,
        "core_count": psutil.cpu_count(),
        "frequency_mhz": cpu_freq.current if cpu_freq else None,
        "frequency_max_mhz": cpu_freq.max if cpu_freq else None
    }

@define_tool(description="Get memory usage statistics")
async def get_memory_stats() -> dict:
    """Get memory statistics."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "percent_used": mem.percent,
        "swap_total_gb": round(swap.total / (1024**3), 2),
        "swap_used_percent": swap.percent
    }

@define_tool(description="Get disk usage for a specific path")
async def get_disk_stats(params: DiskParams) -> dict:
    """Get disk usage statistics."""
    try:
        disk = psutil.disk_usage(params.path)
        return {
            "path": params.path,
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent_used": round(disk.percent, 1)
        }
    except Exception as e:
        return {"error": str(e)}

@define_tool(description="Get network I/O statistics")
async def get_network_stats() -> dict:
    """Get network statistics."""
    net = psutil.net_io_counters()
    
    return {
        "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
        "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2),
        "packets_sent": net.packets_sent,
        "packets_recv": net.packets_recv,
        "errors_in": net.errin,
        "errors_out": net.errout
    }

@define_tool(description="Get list of running processes with resource usage")
async def get_top_processes() -> dict:
    """Get top processes by CPU and memory."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            if info['cpu_percent'] > 0 or info['memory_percent'] > 0.1:
                processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Sort by CPU usage
    processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
    
    return {
        "top_by_cpu": processes[:10],
        "total_processes": len(list(psutil.process_iter()))
    }
```

@define_tool(description="Create a plot from provided data.")
async def create_plot(params: PlotDataParams) -> dict:
    """Create a plot from provided data."""
    os.makedirs(DEFAULT_PLOT_DIR, exist_ok=True)
    
    try:
        data = json.loads(params.data)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON data: {e}"}
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    try:
        
    return {
            "success": True,
            "filepath": os.path.abspath(filepath),
            "message": f"Plot saved to {filepath}"
        }
    except Exception as e:
        plt.close(fig)
        return {"error": str(e)}
```

#### 2.4 Data Visualization Tools

**File: `tools/plotting.py`**
```python
"""Data visualization and plotting tools."""

import os
import json
from datetime import datetime
from pydantic import BaseModel, Field
from copilot import define_tool
from typing import Literal
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

from agent.config import DEFAULT_PLOT_DIR, PLOT_DPI

class PlotDataParams(BaseModel):
    data: str = Field(description="JSON string of data points, e.g., {'x': [1,2,3], 'y': [4,5,6]}")
    title: str = Field(description="Title of the plot")
    x_label: str = Field(default="X", description="Label for X axis")
    y_label: str = Field(default="Y", description="Label for Y axis")
    plot_type: Literal["line", "bar", "scatter", "pie"] = Field(default="line")
    filename: str = Field(description="Output filename (without extension)")

class MultiSeriesPlotParams(BaseModel):
    data: str = Field(description="JSON with multiple series: {'series1': {'x':[], 'y':[]}, ...}")
    title: str = Field(description="Title of the plot")
    x_label: str = Field(default="X", description="Label for X axis")
    y_label: str = Field(default="Y", description="Label for Y axis")
    filename: str = Field(description="Output filename (without extension)")

@define_tool(description="Generate a plot/graph from data and save to filesystem")
async def create_plot(params: PlotDataParams) -> dict:
    """Create a plot from provided data."""
    os.makedirs(DEFAULT_PLOT_DIR, exist_ok=True)
    
    try:
        data = json.loads(params.data)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON data: {e}"}
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    try:
        if params.plot_type == "line":
            ax.plot(data.get("x", []), data.get("y", []), marker='o')
        elif params.plot_type == "bar":
            ax.bar(data.get("x", []), data.get("y", []))
        elif params.plot_type == "scatter":
            ax.scatter(data.get("x", []), data.get("y", []))
        elif params.plot_type == "pie":
            ax.pie(data.get("values", []), labels=data.get("labels", []), autopct='%1.1f%%')
        
        ax.set_title(params.title)
        if params.plot_type != "pie":
            ax.set_xlabel(params.x_label)
            ax.set_ylabel(params.y_label)
            ax.grid(True, alpha=0.3)
        
        filepath = os.path.join(DEFAULT_PLOT_DIR, f"{params.filename}.png")
        plt.savefig(filepath, dpi=PLOT_DPI, bbox_inches='tight')
        plt.close(fig)
        
    return {
            "success": True,
            "filepath": os.path.abspath(filepath),
            "message": f"Plot saved to {filepath}"
        }
    except Exception as e:
        plt.close(fig)
        return {"error": str(e)}
```

---

### Phase 3: Background Job Registry

**File: `registry/job_registry.py`**
```python
"""Background job registry for tracking long-running processes."""

import os
import json
import uuid
from datetime import datetime
from typing import Optional
from agent.config import JOB_REGISTRY_FILE

class JobRegistry:
    """Singleton registry for tracking background jobs."""
    
    _instance = None
    _jobs: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance
    
    def _load(self):
        """Load jobs from disk."""
        if os.path.exists(JOB_REGISTRY_FILE):
            try:
                with open(JOB_REGISTRY_FILE, 'r') as f:
                    self._jobs = json.load(f)
            except:
                self._jobs = {}
        else:
            self._jobs = {}
    
    def _save(self):
        """Persist jobs to disk."""
        with open(JOB_REGISTRY_FILE, 'w') as f:
            json.dump(self._jobs, f, indent=2, default=str)
    
    def register_job(
        self,
        pid: int,
        name: str,
        command: str,
        session_id: str
    ) -> str:
        """Register a new background job."""
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        
        self._jobs[job_id] = {
            "job_id": job_id,
            "pid": pid,
            "name": name,
            "command": command,
            "session_id": session_id,
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "stopped_at": None
        }
        
        self._save()
        return job_id
    
    def get_job(self, job_id: str) -> Optional[dict]:
        """Get a job by ID."""
        return self._jobs.get(job_id)
    
    def list_jobs(self) -> list:
        """List all jobs."""
        return list(self._jobs.values())
    
    def update_job_status(self, job_id: str, status: str):
        """Update job status."""
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = status
            if status in ("stopped", "completed", "failed"):
                self._jobs[job_id]["stopped_at"] = datetime.now().isoformat()
            self._save()
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job from registry."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            self._save()
            return True
        return False
    
    def is_job_running(self, pid: int) -> bool:
        """Check if a process is still running."""
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False
```

---

### Phase 4: Custom Agents

**File: `agents/definitions.py`**
```python
"""Custom agent configurations."""

from copilot import CustomAgentConfig

SYSADMIN_AGENT: CustomAgentConfig = {
    "name": "sysadmin",
    "display_name": "System Administrator",
    "description": "Expert in system administration, process management, and troubleshooting",
    "prompt": """
You are an expert system administrator. Your specialties include:
- Process and service management
- Resource monitoring and optimization
- Shell scripting and automation
- Troubleshooting system issues

When running commands:
- Prefer non-destructive read operations first
- Warn before any potentially dangerous operations
- Suggest background execution for long-running tasks
- Always explain what commands do before running them

Use the available tools to help users manage their system effectively.
""",
    "tools": ["bash", "view", "edit"],
    "infer": True
}

ANALYST_AGENT: CustomAgentConfig = {
    "name": "analyst",
    "display_name": "Data Analyst",
    "description": "Specializes in analyzing system metrics and creating visualizations",
    "prompt": """
You are a data analyst specializing in system performance analysis.

Your expertise includes:
- Collecting and analyzing system metrics
- Creating meaningful visualizations
- Identifying performance trends and anomalies
- Making optimization recommendations

When creating visualizations:
- Choose appropriate chart types for the data
- Use clear, descriptive titles and labels
- Explain what the visualization shows
- Suggest actionable insights based on the data

Always explain your analysis in plain terms.
""",
    "tools": ["view"],
    "infer": True
}

HARDWARE_AGENTS = [SYSADMIN_AGENT, ANALYST_AGENT]
```

---

### Phase 5: Permission Handlers (Hooks)

**File: `hooks/permissions.py`**
```python
"""Permission request handlers for sensitive operations."""

from copilot import PermissionRequest, PermissionRequestResult
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel

console = Console()

# Commands that are always safe
SAFE_COMMANDS = ["ls", "pwd", "whoami", "date", "cat", "head", "tail", "echo", "ps", "top", "df", "free"]

# Commands that require explicit approval
DANGEROUS_COMMANDS = ["rm", "dd", "mkfs", "chmod", "chown", "kill", "pkill", "shutdown", "reboot"]

def on_permission_request(
    request: PermissionRequest,
    invocation: dict
) -> PermissionRequestResult:
    """Handle permission requests from the agent."""
    
    kind = request.get("kind", "unknown")
    
    console.print(Panel(
        f"[yellow]Permission Request[/yellow]\n"
        f"Type: [bold]{kind}[/bold]\n"
        f"Session: {invocation.get('session_id', 'unknown')[:8]}...",
        title="⚠️  Agent Requesting Permission"
    ))
    
    # Handle shell commands
    if kind == "shell":
        command = request.get("command", "")
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
    
    # Default: ask user
    else:
        if Confirm.ask(f"Allow {kind} operation?"):
            return {"kind": "approved"}
        else:
            return {"kind": "denied-interactively-by-user"}
```

---

### Phase 6: Skills Directory

**File: `skills/hardware-expert/SKILL.md`**
```markdown
---
name: hardware-expert
description: Domain expertise for hardware monitoring and system diagnostics
---

# Hardware Expert Knowledge

You have deep expertise in hardware monitoring and system diagnostics.

## Key Metrics to Monitor

### CPU
- **Usage %**: Normal < 70%, Warning 70-90%, Critical > 90%
- **Load Average**: Should be <= number of CPU cores
- **Frequency**: Check for thermal throttling if below max

### Memory
- **Available**: Should have at least 10-20% free
- **Swap Usage**: High swap = memory pressure
- **Cache**: High cache is normal and good

### Disk
- **Usage**: Warning at 80%, Critical at 90%
- **I/O Wait**: High values indicate disk bottleneck
- **SMART status**: Check for drive health

### Network
- **Errors**: Should be near zero
- **Dropped packets**: Indicates buffer issues
- **Bandwidth**: Compare to interface capacity

## Diagnostic Commands

When diagnosing issues, use these commands:
- `top` or `htop`: Real-time process monitoring
- `iostat`: Disk I/O statistics  
- `vmstat`: Virtual memory statistics
- `netstat` or `ss`: Network connections
- `dmesg`: Kernel messages and hardware errors

## Performance Tuning Tips

1. **High CPU**: Identify process with `top`, check for runaway processes
2. **Low Memory**: Check for memory leaks, consider adding swap
3. **Disk Full**: Find large files with `du -sh /*`, clean logs
4. **Network Slow**: Check for packet loss, verify MTU settings
```

---

### Phase 7: Main Agent Client

**File: `agent/client.py`**
```python
"""Main hardware agent client wrapper."""

import asyncio
from rich.console import Console
from copilot import CopilotClient, CopilotSession

from agent.config import DEFAULT_MODEL, LOG_LEVEL
from tools.shell import run_foreground_command, run_background_command
from tools.jobs import list_background_jobs, get_job_status, stop_background_job, remove_job
from tools.hardware import get_cpu_stats, get_memory_stats, get_disk_stats, get_network_stats, get_top_processes
from tools.plotting import create_plot, create_multi_series_plot, create_system_dashboard
from agents.definitions import HARDWARE_AGENTS
from hooks.permissions import on_permission_request

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
    """Hardware monitoring and management agent."""
    
    def __init__(self):
        self.client: CopilotClient | None = None
        self.session: CopilotSession | None = None
    
    async def initialize(self):
        """Initialize the Copilot client and create session."""
        console.print("[blue]Initializing Hardware Agent...[/blue]")
        
        self.client = CopilotClient({
            "log_level": LOG_LEVEL,
            "auto_start": True
        })
        
        await self.client.start()
        
        # Create session with all features
        self.session = await self.client.create_session({
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
            "system_message": {
                "mode": "append",
                "content": SYSTEM_INSTRUCTIONS
            },
            
            # Load skills from directory
            "skill_directories": ["./skills"],
        })
        
        # Set up event handlers
        self._setup_event_handlers()
        
        console.print("[green]✓ Hardware Agent ready![/green]")
    
    def _setup_event_handlers(self):
        """Configure event handlers for streaming and status."""
        self.session.on(self._handle_event)
    
    def _handle_event(self, event):
        """Process session events."""
        event_type = event.type.value if hasattr(event.type, 'value') else event.type
        
        if event_type == "assistant.message_delta":
            # Stream response chunks
            delta = getattr(event.data, 'delta_content', '')
            if delta:
                console.print(delta, end='')
        
        elif event_type == "tool.execution_start":
            tool_name = getattr(event.data, 'tool_name', 'unknown')
            console.print(f"\n[dim]🔧 Running: {tool_name}...[/dim]")
        
        elif event_type == "tool.execution_complete":
            console.print("[dim]✓[/dim]", end=' ')
        
        elif event_type == "subagent.selected":
            agent_name = getattr(event.data, 'agent_display_name', 'unknown')
            console.print(f"\n[magenta]🤖 Agent: {agent_name}[/magenta]")
        
        elif event_type == "session.idle":
            console.print()  # New line after response
    
    async def send(self, prompt: str):
        """Send a message to the agent."""
        if not self.session:
            raise RuntimeError("Agent not initialized")
        
        await self.session.send({"prompt": prompt})
    
    async def send_and_wait(self, prompt: str):
        """Send a message and wait for complete response."""
        if not self.session:
            raise RuntimeError("Agent not initialized")
        
        return await self.session.send_and_wait({"prompt": prompt})
    
    async def shutdown(self):
        """Clean up resources."""
        console.print("\n[yellow]Shutting down...[/yellow]")
        
        if self.session:
            await self.session.destroy()
        
        if self.client:
            await self.client.stop()
        
        console.print("[green]Goodbye![/green]")
```

---

### Phase 8: CLI Entry Point

**File: `main.py`**
```python
#!/usr/bin/env python3
"""Hardware Agent CLI - Main entry point."""

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

async def main():
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
                console.print("[bold cyan]Agent:[/bold cyan] ", end='')
                
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
```

---

## 🎯 Features Demonstrated

| SDK Feature | Implementation |
|-------------|----------------|
| **Custom Tools** | 12 tools across shell, jobs, hardware, plotting |
| **MCP Servers** | Ready for integration (optional) |
| **Custom Agents** | SysAdmin and Data Analyst agents |
| **Permission Handlers** | Interactive approval for dangerous operations |
| **Custom Instructions** | System message with domain context |
| **Skill Directories** | hardware-expert skill loaded from file |
| **Streaming** | Real-time response display |
| **Event Handling** | Rich event processing for all event types |
| **Session Management** | Full lifecycle management |

---

## 🚀 Running the Agent

```bash
# Navigate to project
cd samples/hardware-agent

# Install dependencies
pip install -r requirements.txt

# Run the agent
python main.py
```

---

## 📝 Example Interactions

```
You: Show me current system stats

Agent: 🔧 Running: get_cpu_stats...
       🔧 Running: get_memory_stats...
       
Here's your current system status:

**CPU**: 23.5% average usage across 8 cores
**Memory**: 12.4 GB used of 32 GB (38.8%)
**Swap**: Minimal usage at 2.1%

Everything looks healthy! Would you like me to create a dashboard visualization?

You: Yes, and also run a stress test in the background

⚠️  Agent Requesting Permission
Type: shell
Command: stress --cpu 4 --timeout 60

Allow this command? [y/n]: y

Agent: I've started the stress test as a background job:
- Job ID: job_a1b2c3d4
- PID: 12345
- Status: running

The dashboard has been saved to ./plots/dashboard_20240122_143022.png

You: jobs

Agent: Current background jobs:
┌────────────────┬───────┬─────────┬────────────────────┐
│ Job ID         │ PID   │ Status  │ Command            │
├────────────────┼───────┼─────────┼────────────────────┤
│ job_a1b2c3d4   │ 12345 │ running │ stress --cpu 4...  │
└────────────────┴───────┴─────────┴────────────────────┘
```
