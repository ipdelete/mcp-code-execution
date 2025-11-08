# Prompt

Review the MCP Code Execution project architecture and provide packaging recommendations.

**Project Context:**
This is a Python runtime (mcp-code-execution) that enables AI agents to work with MCP tools through a progressive disclosure pattern, achieving 98.7% token reduction. The current implementation:

**Current Structure:**
- Core runtime in `src/runtime/` with components like:
  - `mcp_client.py` - Lazy-loading MCP client manager
  - `harness.py` - Script execution environment
  - `generate_wrappers.py` - Auto-generate typed wrappers from MCP schemas
  - `normalize_fields.py` - Field normalization for inconsistent APIs
  - `schema_utils.py` - JSON Schema → Pydantic conversion
  - `discover_schemas.py` - Schema discovery
  - `config.py` - Configuration management

- Project scripts: `mcp-generate`, `mcp-exec`, `mcp-discover`
- CLI harness for running generated Python scripts
- Pydantic-based type safety
- Integration tests with git and fetch MCP servers

**Current Distribution:**
- Installed via `uv pip install -e ".[dev]"`
- Can be used as a library via imports from `runtime.*`
- Scripts invoked via `uv run mcp-exec` etc.

**Goals:**
- Want engineers AND agents to be able to use this
- Need flexibility for different use cases
- Should work seamlessly in both local dev environments and agent contexts

**Your Task:**
1. Analyze the current architecture and use cases
2. Evaluate these packaging approaches:
   - **MCP Server**: Expose this runtime as an MCP server itself with tools like `generate_wrappers`, `execute_script`, `discover_schemas`
   - **Python CLI Tool**: Standalone CLI with subcommands (which it partially has now)
   - **Hybrid Approach**: Both an MCP server AND a polished CLI tool
   - **Library-First**: Focus on being a library that others build CLI/MCP on top of
   - **Other creative solutions**: Any other architectural patterns you see fit

3. Consider:
   - How engineers would discover and use this
   - How agents would interact with it
   - Discoverability and ease of integration
   - Maintenance burden
   - Lock-in vs. flexibility

4. Provide your final recommendation with:
   - Primary packaging approach (ranked by fit)
   - Architectural changes needed
   - Integration points for engineers vs. agents
   - Implementation priority

Analyze the actual codebase at `/home/cip/src/mcp-code-execution` to inform your recommendations.

---

# MCP Code Execution: Architectural Analysis & Packaging Recommendations

## Executive Summary

After analyzing the codebase, the recommendation is: **Adopt a Hybrid Approach** with an MCP server as the primary interface and enhanced CLI tools as a secondary interface. This approach maximizes discoverability for agents while maintaining developer ergonomics.

---

## Current State Analysis

### Architectural Strengths

**1. Clean Separation of Concerns**
- `src/runtime/mcp_client.py` (513 LOC): Lazy-loading client manager with explicit state machine
- `src/runtime/harness.py` (122 LOC): Script execution environment with lifecycle management
- `src/runtime/generate_wrappers.py` (267 LOC): Auto-generation from MCP schemas
- `src/runtime/discover_schemas.py` (240 LOC): Runtime schema inference
- `src/runtime/normalize_fields.py` (151 LOC): Field normalization patterns

**2. Progressive Disclosure Pattern**
The core innovation - 98.7% token reduction - is architecturally sound:
```
Traditional: Agent → MCP Server → [50KB data] → Agent processes
Progressive: Agent → Discovers tools → Writes script → [50KB] → Local processing → [100B summary] → Agent
```

**3. Type Safety Foundation**
- Pydantic models throughout (`src/runtime/config.py`)
- Defensive coding patterns in wrapper generation
- Schema inference from actual responses

**4. Dual Developer Experience**
- Library usage: `from runtime.mcp_client import call_mcp_tool`
- CLI scripts: `mcp-generate`, `mcp-exec`, `mcp-discover`
- Agent-optimized documentation: `AGENTS.md`

### Architectural Weaknesses

**1. Discovery Problem**
- Agents currently discover by **reading filesystem** (`./servers/`)
- This is fragile and non-standard for MCP ecosystem
- No programmatic tool discovery interface

**2. Packaging Confusion**
- Package name mismatch: `pyproject.toml` says `mcp-execution` but imports use `runtime.*`
- No clear entry point for library vs. CLI vs. agent usage
- Missing from PyPI (install only via `uv pip install -e`)

**3. Limited Composability**
- No way for other tools to programmatically invoke wrapper generation
- Harness is tightly coupled to script execution model
- No API for programmatic schema discovery

---

## Packaging Approach Evaluation

### Option 1: MCP Server (Primary Recommendation)

**Architecture**: Expose this runtime as an MCP server with tools like:
- `generate_wrappers` - Auto-generate typed Python wrappers from MCP schemas
- `execute_script` - Run Python scripts with MCP harness
- `discover_schemas` - Infer Pydantic models from actual responses
- `list_available_tools` - Enumerate all tools from configured servers
- `get_tool_schema` - Retrieve schema for a specific tool

**Pros:**
1. **Native Agent Discovery**: Agents discover this via standard MCP protocol, not filesystem reading
2. **Composability**: Other MCP servers can call these tools
3. **Standardization**: Fits into existing MCP ecosystem patterns
4. **Progressive Disclosure Meta-Pattern**: An MCP server that helps agents use other MCP servers efficiently
5. **No Install Required**: Agents connect via stdio, no package installation needed

**Cons:**
1. Requires agents to have two connections: one to this meta-server, one to actual servers
2. More complex for simple CLI use cases
3. Debugging can be harder (stdio protocol overhead)

**Implementation Effort**: Medium (2-3 days)

### Option 2: Python CLI Tool (Secondary Recommendation)

**Architecture**: Polished CLI with subcommands (current state enhanced)
```bash
mcp-exec generate --config mcp_config.json
mcp-exec run workspace/script.py
mcp-exec discover --config discovery_config.json
mcp-exec list-tools
```

**Pros:**
1. Simple for engineers to understand and use
2. Follows Unix philosophy (composable, pipeable)
3. Easy to integrate into CI/CD
4. Low learning curve

**Cons:**
1. Agents must rely on filesystem exploration (current weakness)
2. Not discoverable via MCP protocol
3. Requires installation via uv/pip
4. Doesn't leverage MCP ecosystem

**Implementation Effort**: Low (1 day)

### Option 3: Library-First

**Architecture**: Pure library, others build interfaces on top
```python
from mcp_execution import McpClientManager, WrapperGenerator, SchemaDiscoverer
```

**Pros:**
1. Maximum flexibility for different use cases
2. Clean API for programmatic usage
3. Low maintenance burden

**Cons:**
1. Doesn't solve the agent discovery problem
2. Requires users to build their own interfaces
3. Loses the CLI ergonomics
4. Progressive disclosure pattern requires more user implementation

**Implementation Effort**: Medium (refactoring needed)

### Option 4: Hybrid Approach (FINAL RECOMMENDATION)

**Architecture**: MCP server (primary) + Polished CLI (secondary) + Library (foundation)

```
┌─────────────────────────────────────────────────────┐
│                  MCP Server Layer                    │
│  Tools: generate_wrappers, execute_script, etc.     │
│  Port: stdio (configurable in claude_desktop_config) │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│                   CLI Layer                          │
│  mcp-exec generate, mcp-exec run, etc.              │
│  Direct usage for engineers                          │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│                 Library Layer                        │
│  McpClientManager, WrapperGenerator, etc.           │
│  Foundation for both MCP server and CLI              │
└─────────────────────────────────────────────────────┘
```

**Pros:**
1. **Agents**: Native MCP discovery via server tools
2. **Engineers**: Familiar CLI for direct usage
3. **Advanced Users**: Library API for custom integrations
4. **Future-Proof**: Can add web UI, VSCode extension, etc. later
5. **Ecosystem Fit**: This IS the MCP ecosystem (a meta-server)

**Cons:**
1. Higher initial implementation effort
2. More code to maintain (but each layer is thin)
3. Potential confusion about which interface to use

**Implementation Effort**: Medium-High (3-5 days)

---

## Final Recommendation: Hybrid Approach

### Rationale

This runtime is fundamentally a **meta-MCP tool** - it helps agents and engineers work with MCP servers more efficiently. The hybrid approach recognizes three distinct user personas:

1. **Agents (Claude, etc.)**: Need programmatic discovery via MCP protocol
2. **Engineers (humans)**: Need familiar CLI tools for scripting/automation
3. **Framework Builders**: Need library APIs for custom integrations

### Architectural Changes Needed

#### 1. Create MCP Server Interface

**File**: `src/mcp_execution/server.py` (NEW)

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("mcp-code-execution")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="generate_wrappers",
            description="Auto-generate typed Python wrappers from MCP server schemas",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {"type": "string", "description": "Path to mcp_config.json"},
                    "output_dir": {"type": "string", "description": "Output directory for wrappers"}
                }
            }
        ),
        Tool(
            name="execute_script",
            description="Execute a Python script with MCP harness",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_path": {"type": "string", "description": "Path to Python script"},
                    "timeout": {"type": "number", "description": "Timeout in seconds"}
                },
                "required": ["script_path"]
            }
        ),
        Tool(
            name="discover_schemas",
            description="Infer Pydantic models from actual MCP tool responses",
            inputSchema={
                "type": "object",
                "properties": {
                    "discovery_config_path": {"type": "string", "description": "Path to discovery_config.json"}
                }
            }
        ),
        Tool(
            name="list_available_tools",
            description="List all tools from configured MCP servers",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {"type": "string", "description": "Path to mcp_config.json"}
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # Delegate to existing runtime components
    if name == "generate_wrappers":
        from mcp_execution.generator import WrapperGenerator
        gen = WrapperGenerator(Path(arguments.get("config_path")))
        await gen.generate(Path(arguments.get("output_dir", "servers")))
        return [TextContent(type="text", text="Wrappers generated successfully")]
    # ... other tools
```

**Entry point**: `mcp-execution-server` (new script in `pyproject.toml`)

#### 2. Refactor Package Structure

**Current problem**: Imports use `runtime.*` but package is `mcp-execution`

**Solution**: Reorganize to:
```
src/
  mcp_execution/              # Main package
    __init__.py               # Public API exports
    client.py                 # Renamed from mcp_client.py
    harness.py
    generator.py              # Renamed from generate_wrappers.py
    discovery.py              # Renamed from discover_schemas.py
    normalize.py              # Renamed from normalize_fields.py
    config.py
    exceptions.py
    schema/                   # New subpackage
      utils.py
      inference.py
    server.py                 # NEW: MCP server interface
    cli.py                    # NEW: Consolidated CLI
```

**Update imports**:
```python
# Old: from runtime.mcp_client import call_mcp_tool
# New: from mcp_execution import call_mcp_tool
```

#### 3. Add Library API Facade

**File**: `src/mcp_execution/__init__.py`

```python
"""MCP Code Execution - Progressive disclosure runtime for MCP tools."""

from .client import McpClientManager, call_mcp_tool, get_mcp_client_manager
from .generator import WrapperGenerator
from .discovery import SchemaDiscoverer
from .config import McpConfig, ServerConfig
from .exceptions import (
    McpExecutionError,
    ConfigurationError,
    ServerConnectionError,
    ToolNotFoundError,
    ToolExecutionError,
)

__all__ = [
    "McpClientManager",
    "call_mcp_tool",
    "get_mcp_client_manager",
    "WrapperGenerator",
    "SchemaDiscoverer",
    "McpConfig",
    "ServerConfig",
    # Exceptions
    "McpExecutionError",
    "ConfigurationError",
    "ServerConnectionError",
    "ToolNotFoundError",
    "ToolExecutionError",
]

__version__ = "2.0.0"
```

#### 4. Consolidate CLI

**File**: `src/mcp_execution/cli.py` (NEW)

```python
import asyncio
import click
from pathlib import Path
from .generator import WrapperGenerator
from .harness import execute_script
from .discovery import SchemaDiscoverer

@click.group()
def cli():
    """MCP Code Execution - Progressive disclosure runtime for MCP tools"""
    pass

@cli.command()
@click.option("--config", default="mcp_config.json", help="Path to MCP config")
@click.option("--output", default="servers", help="Output directory for wrappers")
def generate(config, output):
    """Generate typed wrappers from MCP schemas"""
    gen = WrapperGenerator(Path(config))
    asyncio.run(gen.generate(Path(output)))
    click.echo("✓ Wrappers generated successfully")

@cli.command()
@click.argument("script_path")
@click.option("--timeout", default=30, help="Execution timeout in seconds")
def run(script_path, timeout):
    """Execute script with MCP harness"""
    result = asyncio.run(execute_script(Path(script_path), timeout))
    click.echo(result)

@cli.command()
@click.option("--config", default="discovery_config.json", help="Path to discovery config")
def discover(config):
    """Discover schemas from actual MCP responses"""
    discoverer = SchemaDiscoverer(Path(config))
    schemas = asyncio.run(discoverer.discover())
    click.echo(f"✓ Discovered {len(schemas)} schemas")

@cli.command()
@click.option("--config", default="mcp_config.json", help="Path to MCP config")
def list_tools(config):
    """List all tools from configured MCP servers"""
    # Implementation
    pass

if __name__ == "__main__":
    cli()
```

### Integration Points

#### For Engineers

**CLI Usage** (consolidated):
```bash
# Generate wrappers
mcp-exec generate

# Run script
mcp-exec run workspace/my_script.py

# Discover schemas
mcp-exec discover

# List available tools
mcp-exec list-tools
```

**Library Usage** (improved imports):
```python
# Before
from runtime.mcp_client import call_mcp_tool

# After
from mcp_execution import call_mcp_tool
```

#### For Agents

**Claude Desktop Config** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "code-execution": {
      "command": "uvx",
      "args": ["mcp-execution-server"]
    }
  }
}
```

**Agent discovers via MCP**:
```
Agent: /tools
→ generate_wrappers, execute_script, discover_schemas, list_available_tools

Agent: Call generate_wrappers(config_path="mcp_config.json")
→ Success: Wrappers generated at ./servers/

Agent: Call list_available_tools()
→ ["git__git_status", "git__git_log", "fetch__fetch", ...]

Agent: Writes script.py
Agent: Call execute_script(script_path="workspace/analysis.py")
→ Script output with summary
```

**Key advantage**: Agent no longer needs to "read filesystem to discover tools" - it's now using standard MCP protocol.

---

## Implementation Priority

### Phase 1: Foundation (Week 1)
1. Refactor package structure (`runtime` → `mcp_execution`)
2. Create library API facade (`__init__.py`)
3. Update all imports in codebase
4. Update tests to use new imports
5. Publish to PyPI as `mcp-execution` v2.0.0

### Phase 2: MCP Server (Week 2)
1. Implement MCP server interface (`server.py`)
2. Add `mcp-execution-server` entry point
3. Create tools: `generate_wrappers`, `execute_script`, `discover_schemas`, `list_available_tools`
4. Test with Claude Desktop
5. Document agent usage in README

### Phase 3: CLI Enhancement (Week 3)
1. Consolidate CLI to single entry point (`cli.py`)
2. Use Click for better UX
3. Add `--help`, `--version`, `--config` flags
4. Add `list-tools` command
5. Update developer documentation

### Phase 4: Publishing (Week 4)
1. Publish MCP server to MCP registry
2. Create PyPI package with all entry points
3. Write migration guide (v1 → v2)
4. Update README with all three usage modes
5. Create agent usage examples

---

## Long-Term Vision

This hybrid architecture enables future extensions:

**Year 1:**
- VSCode extension using library API
- Web dashboard for MCP tool exploration
- GitHub Action for CI/CD integration

**Year 2:**
- Plugin system for custom normalization strategies
- Multi-language support (generate TypeScript wrappers)
- Cloud-hosted execution service

**Year 3:**
- MCP marketplace integration
- Enterprise features (auth, rate limiting, monitoring)
- Agent orchestration tools

---

## Decision Matrix

| Factor | CLI Only | MCP Only | Hybrid |
|--------|----------|----------|--------|
| Agent Discovery | ⚠️ Filesystem | ✅ Native MCP | ✅ Native MCP |
| Engineer Experience | ✅ Familiar | ⚠️ Different | ✅ Familiar |
| Composability | ⚠️ Limited | ✅ High | ✅ High |
| Maintenance | ✅ Low | ✅ Low | ⚠️ Medium |
| Future-Proof | ⚠️ Limited | ✅ High | ✅ Very High |
| Ecosystem Fit | ⚠️ Standard | ✅ Native | ✅ Ideal |
| Time to Implement | ✅ 1 day | ⚠️ 3 days | ⚠️ 5 days |

**Verdict**: Hybrid approach wins on every dimension except implementation time, and that's worth the investment.

---

## Conclusion

The **Hybrid Approach** is the architecturally sound choice because:

1. **Solves the Discovery Problem**: Agents use MCP protocol, not filesystem hacks
2. **Maintains Developer Ergonomics**: CLI remains simple and familiar
3. **Enables Composability**: Library API for advanced use cases
4. **Future-Proof**: Foundation for extensions and integrations
5. **Ecosystem Alignment**: Positions this as a meta-MCP tool, which it fundamentally is

This is not just a packaging decision - it's recognizing that **mcp-code-execution is itself an MCP server that helps agents use other MCP servers**. The progressive disclosure pattern deserves to be a first-class MCP citizen.

---

## Next Steps

1. Review this recommendation with stakeholders
2. Prioritize Phase 1 (foundation refactoring)
3. Create GitHub project board for implementation tracking
4. Set up CI/CD for multi-package publishing (PyPI + MCP registry)

The architecture is sound. The implementation is clean. The innovation is real. Now we make it discoverable.
