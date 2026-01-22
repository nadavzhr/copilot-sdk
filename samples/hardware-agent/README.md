# Hardware Agent CLI

A proof-of-concept Python CLI tool that demonstrates modern agentic workflow features of the GitHub Copilot SDK. The agent specializes in hardware monitoring, system diagnostics, and data visualization.

## Features

- **Shell Command Execution**: Run commands in foreground or background
- **Background Job Registry**: Track and manage long-running processes
- **Data Visualization**: Generate graphs/plots from system metrics
- **Hardware Monitoring**: CPU, memory, disk, network statistics
- **Custom Agents**: Specialized SysAdmin and Data Analyst agents
- **Permission Handlers**: Interactive approval for sensitive operations
- **Skills Directory**: Domain knowledge for hardware expertise

## Prerequisites

Before running the Hardware Agent, ensure you have:

1. **Python 3.8+** installed
2. **GitHub Copilot CLI** installed and authenticated:
   - Install from: https://docs.github.com/en/copilot/github-copilot-in-the-cli
   - Verify installation: `copilot --version`
   - Authenticate: `copilot auth login`

> **Note for Windows users**: After installing the Copilot CLI, you may need to restart your terminal or add the installation directory to your PATH.

## Installation

```bash
# Navigate to project
cd samples/hardware-agent

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the agent
python main.py
```

### Slash Commands

| Command | Description |
|---------|-------------|
| `/cpu` | Show CPU statistics |
| `/memory` | Show memory usage |
| `/disk` | Show disk usage |
| `/network` | Show network stats |
| `/dashboard` | Generate system dashboard |
| `/jobs` | List background jobs |
| `/top` | Show top processes |
| `/help` | Show help message |
| `/clear` | Clear the screen |
| `/quit` | Exit the agent |

### Natural Language

Just type naturally to interact with the agent:

```
You: Show me current CPU and memory usage
```

### Example Session

```
You: /cpu

╭─────────────────────────────────────── Agent ───────────────────────────────────────╮
│ ## CPU Statistics                                                                    │
│                                                                                      │
│ **Overall Usage**: 23.5%                                                            │
│ **Core Count**: 8 cores                                                             │
│ **Frequency**: 2800 MHz (max: 3600 MHz)                                             │
│                                                                                      │
│ ✓ CPU usage is normal. Values below 70% indicate healthy performance.               │
╰──────────────────────────────────────────────────────────────────────────────────────╯

You: Create a dashboard and save it

╭─────────────────────────────────────── Agent ───────────────────────────────────────╮
│ I've created a comprehensive system dashboard with:                                  │
│ - CPU usage by core                                                                 │
│ - Memory allocation                                                                 │
│ - Disk usage                                                                        │
│ - Network I/O                                                                       │
│                                                                                      │
│ Dashboard saved to: ./plots/dashboard_20240122_143022.png                           │
╰──────────────────────────────────────────────────────────────────────────────────────╯
```

## Project Structure

```
samples/hardware-agent/
├── PLAN.md                    # Implementation plan
├── README.md                  # This file
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
│   └── definitions.py         # Custom agent configurations
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

## SDK Features Demonstrated

| SDK Feature | Implementation |
|-------------|----------------|
| **Custom Tools** | 12 tools across shell, jobs, hardware, plotting |
| **Custom Agents** | SysAdmin and Data Analyst agents |
| **Permission Handlers** | Interactive approval for dangerous operations |
| **Custom Instructions** | System message with domain context |
| **Skill Directories** | hardware-expert skill loaded from file |
| **Streaming** | Real-time response display |
| **Event Handling** | Rich event processing for all event types |
| **Session Management** | Full lifecycle management |

## Architecture

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

## Troubleshooting

### "The system cannot find the file specified" (Windows)

This error occurs when the GitHub Copilot CLI is not installed or not in your PATH.

**Solution:**
1. Install the GitHub Copilot CLI: https://docs.github.com/en/copilot/github-copilot-in-the-cli
2. Restart your terminal after installation
3. Verify with: `copilot --version`
4. If still not working, set `COPILOT_CLI_PATH` environment variable to the full path of the executable

### "copilot: command not found" (macOS/Linux)

**Solution:**
1. Install the GitHub Copilot CLI
2. Add the installation directory to your PATH
3. Run: `copilot auth login` to authenticate

### Authentication errors

**Solution:**
1. Run `copilot auth status` to check your authentication status
2. Run `copilot auth login` to authenticate or re-authenticate

## License

This sample is part of the GitHub Copilot SDK and is licensed under the same terms.
