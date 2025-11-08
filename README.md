# MCP Code Execution - Python Runtime

**98.7% Token Reduction** through progressive tool discovery for Model Context Protocol (MCP) servers.

## Overview

This runtime enables AI agents to work with MCP tools through a progressive disclosure pattern:
1. Agent explores `./servers/` to discover available tools
2. Agent reads only needed tool definitions
3. Agent writes Python script that processes data locally
4. Script returns summary only (not raw data)

**Result**: ~98.7% reduction in tokens sent to the agent.

## Features

- 🦥 **Lazy Loading**: Servers connect only when tools are called
- 🔒 **Type Safety**: Pydantic models for all tool inputs/outputs
- 🔄 **Defensive Coding**: Handles variable MCP response structures
- 📦 **Auto-generated Wrappers**: Typed Python functions from MCP schemas
- 🛠️ **Field Normalization**: Handles inconsistent API casing (e.g., ADO)

## Installation

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Node.js (for MCP servers)

### Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/ipdelete/mcp-code-execution.git
cd mcp-code-execution

# Install dependencies
uv sync --all-extras

# Install in editable mode
uv pip install -e ".[dev]"
```

## Quick Start

### 1. Configure MCP Servers

Create `mcp_config.json`:

```json
{
  "mcpServers": {
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "."]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    }
  }
}
```

### 2. Generate Tool Wrappers

```bash
uv run mcp-generate
```

This creates typed wrappers in `src/servers/`:

```
src/servers/
  git/
    __init__.py
    git_status.py
    git_log.py
    git_diff.py
  fetch/
    __init__.py
    fetch.py
```

### 3. How It Works

When you ask an AI agent to work with your data:

1. **Agent explores** the available MCP tools via `./servers/`
2. **Agent writes a script** that uses `call_mcp_tool()` to fetch data from MCP servers
3. **Script processes locally** - the MCP server returns full data, but the script processes it and returns only a summary
4. **Agent receives summary** - keeping context lean and token usage minimal

Example script the agent might write:

```python
"""Analyze git repository commits."""

import asyncio
from runtime.mcp_client import call_mcp_tool

async def main():
    # Fetch recent commits
    result = await call_mcp_tool(
        "git__git_log",
        {"repo_path": ".", "max_count": 10}
    )

    # Process locally
    print(f"Found {len(result)} commits")

    # Return summary (not full data)
    return {"commit_count": len(result)}

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Agent Execution

When the agent needs to run a script, it uses the harness:

```bash
# The agent runs this automatically
uv run python -m runtime.harness workspace/my_script.py

# Or via the convenience alias
uv run mcp-exec workspace/my_script.py
```

The harness manages the MCP client lifecycle, connects to servers, and captures the script's output to send back to the agent.

## Architecture

### Progressive Disclosure Pattern

**Traditional Approach** (High Token Usage):
```
Agent → MCP Server → [Full Data 50KB] → Agent processes all
```

**Progressive Disclosure** (98.7% Reduction):
```
Agent → Discovers tools → Writes script
Script → MCP Server → [Full Data 50KB] → Processes locally → [Summary 100B] → Agent
```

### Key Components

- **`runtime/mcp_client.py`**: Lazy-loading MCP client manager
- **`runtime/harness.py`**: Script execution environment
- **`runtime/generate_wrappers.py`**: Auto-generate typed wrappers
- **`runtime/normalize_fields.py`**: Handle API field casing
- **`runtime/schema_utils.py`**: JSON Schema → Pydantic conversion

## Development

### Running Tests

```bash
# All tests
uv run pytest

# Unit tests only
uv run pytest tests/unit/

# Integration tests
uv run pytest tests/integration/

# With coverage
uv run pytest --cov=src/runtime
```

### Code Quality

```bash
# Type checking
uv run mypy src/

# Formatting
uv run black src/ tests/

# Linting
uv run ruff check src/ tests/

# Format check
uv run black --check src/ tests/
```

### Project Scripts

```bash
# Generate wrappers
uv run mcp-generate

# Execute script
uv run mcp-exec workspace/script.py

# Discover schemas (optional)
uv run mcp-discover
```

## Python-Specific Features

### Type Safety with Pydantic

All tool parameters and results are validated with Pydantic:

```python
from runtime.servers.git import git_status, GitStatusParams

# Type-safe parameters
params = GitStatusParams(repo_path=".")

# Type-safe result
result = await git_status(params)
```

### Async/Await Support

Built on `asyncio` for efficient I/O:

```python
import asyncio
from runtime.mcp_client import call_mcp_tool

async def main():
    # Concurrent tool calls
    results = await asyncio.gather(
        call_mcp_tool("git__git_status", {"repo_path": "."}),
        call_mcp_tool("git__git_log", {"repo_path": ".", "max_count": 5}),
    )

asyncio.run(main())
```

### Field Normalization

Handles inconsistent API casing automatically:

```python
from runtime.normalize_fields import normalize_field_names

# ADO returns lowercase, expects PascalCase
ado_response = {"system.title": "Task", "custom.priority": "High"}
normalized = normalize_field_names(ado_response, "ado")
# Result: {"System.title": "Task", "Custom.priority": "High"}
```

## Examples

See `workspace/example_progressive_disclosure.py` for a complete example demonstrating the token reduction pattern.

## Contributing

```bash
# Install dev dependencies
uv sync --all-extras

# Run quality checks before committing
uv run black src/ tests/
uv run mypy src/
uv run ruff check src/ tests/
uv run pytest
```

## License

MIT

## References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
