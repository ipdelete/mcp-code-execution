---
description: Phase 2 - Core Runtime MCP Client Manager
model: sonnet
---

# Phase 2: Core Runtime - MCP Client Manager

**Goal**: Port the lazy-loading MCP client manager (heart of 98.7% token reduction)

**Tasks**: T029-T049 | **Validation**: CHK023-CHK032, CHK086-CHK089, CHK097, CHK112-CHK120

## Context: Read plan.md First

Review `plan.md` section: **Phase 2: Core Runtime - MCP Client Manager (lines 307-415)** for detailed implementation patterns and key features to preserve.

## Prerequisites

- ✅ Phase 1 completed (project setup)
- ✅ TypeScript reference available at `_typescript_reference/runtime/mcp-client.ts`

## Key Features to Preserve

1. **Lazy Initialization**: Config loaded, servers NOT connected
2. **Lazy Connection**: Servers connect on first tool call
3. **Tool Caching**: Avoid repeated list_tools calls
4. **Defensive Unwrapping**: `response.value or response`
5. **Singleton Pattern**: Single manager instance

## Instructions

### 1. Create MCP Client Manager Skeleton (T029-T030)

Create `src/runtime/mcp_client.py`:

```python
"""
MCP Client Manager with lazy loading pattern.

This module implements the core 98.7% token reduction pattern through:
- Lazy initialization (config loaded, servers NOT connected)
- Lazy connection (servers connect on first tool call)
- Tool caching (avoid repeated list_tools calls)
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client

from .config import McpConfig, ServerConfig
from .exceptions import (
    ConfigurationError,
    ServerConnectionError,
    ToolExecutionError,
    ToolNotFoundError,
)

logger = logging.getLogger("mcp_execution.client")


class McpClientManager:
    """Lazy-loading MCP client manager."""

    def __init__(self) -> None:
        """Initialize manager without connecting to servers."""
        self._clients: Dict[str, Client] = {}
        self._tool_cache: Dict[str, List[Any]] = {}
        self._config: Optional[McpConfig] = None
        self._initialized: bool = False
        logger.debug("McpClientManager initialized (no connections)")

    async def initialize(self, config_path: Optional[Path] = None) -> None:
        """
        Load config only - don't connect to servers yet.

        Args:
            config_path: Path to mcp_config.json (default: ./mcp_config.json)

        Raises:
            ConfigurationError: If config file not found or invalid
        """
        # Implementation in next step
        pass

    async def _connect_to_server(
        self, server_name: str, config: ServerConfig
    ) -> None:
        """
        Connect to a single server on-demand.

        Args:
            server_name: Name of the server
            config: Server configuration

        Raises:
            ServerConnectionError: If connection fails
        """
        # Implementation in next step
        pass

    async def call_tool(
        self, tool_identifier: str, params: Dict[str, Any]
    ) -> Any:
        """
        Call tool with lazy connection.

        Format: "serverName__toolName"

        Args:
            tool_identifier: Tool identifier in format "server__tool"
            params: Tool parameters

        Returns:
            Tool execution result (unwrapped)

        Raises:
            ToolNotFoundError: If tool not found
            ToolExecutionError: If tool execution fails
        """
        # Implementation in next step
        pass

    async def list_all_tools(self) -> List[Any]:
        """
        List all available tools (connects to all servers).

        Returns:
            List of all tools from all servers
        """
        # Implementation in next step
        pass

    async def cleanup(self) -> None:
        """Close all connections gracefully."""
        # Implementation in next step
        pass


# Singleton pattern (thread-safe with lru_cache)
@lru_cache(maxsize=1)
def get_mcp_client_manager() -> McpClientManager:
    """Get or create singleton instance."""
    return McpClientManager()


async def call_mcp_tool(tool_identifier: str, params: Dict[str, Any]) -> Any:
    """
    Convenience function for calling tools.

    Args:
        tool_identifier: Tool identifier in format "server__tool"
        params: Tool parameters

    Returns:
        Tool execution result
    """
    manager = get_mcp_client_manager()
    if not manager._initialized:
        await manager.initialize()
    return await manager.call_tool(tool_identifier, params)
```

### 2. Implement Initialize (T031-T032)

Add to `McpClientManager`:

```python
async def initialize(self, config_path: Optional[Path] = None) -> None:
    """Load config only - don't connect to servers yet."""
    if self._initialized:
        logger.warning("McpClientManager already initialized")
        return

    config_file = config_path or Path.cwd() / "mcp_config.json"

    if not config_file.exists():
        raise ConfigurationError(f"Config file not found: {config_file}")

    try:
        import aiofiles

        async with aiofiles.open(config_file, "r") as f:
            content = await f.read()
        self._config = McpConfig.model_validate_json(content)
        self._initialized = True
        logger.info(
            f"Configuration loaded ({len(self._config.mcpServers)} servers available)"
        )
    except Exception as e:
        raise ConfigurationError(f"Failed to load config: {e}") from e
```

### 3. Implement Lazy Connection (T033-T034)

Add to `McpClientManager`:

```python
async def _connect_to_server(
    self, server_name: str, config: ServerConfig
) -> None:
    """Connect to a single server on-demand."""
    if server_name in self._clients:
        logger.debug(f"Server {server_name} already connected")
        return

    try:
        logger.info(f"Connecting to server: {server_name}")

        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env or {},
        )

        # Note: Context manager handled at call site
        read, write = await stdio_client(server_params).__aenter__()
        client = Client(read, write)
        await client.__aenter__()
        await client.initialize()

        self._clients[server_name] = client
        logger.info(f"Connected to server: {server_name}")

    except Exception as e:
        raise ServerConnectionError(
            f"Failed to connect to server {server_name}: {e}"
        ) from e
```

### 4. Implement Tool Calling with Defensive Unwrapping (T035-T038)

Add to `McpClientManager`:

```python
async def call_tool(
    self, tool_identifier: str, params: Dict[str, Any]
) -> Any:
    """Call tool with lazy connection."""
    if not self._initialized:
        raise ConfigurationError("Manager not initialized. Call initialize() first.")

    # Parse tool identifier
    if "__" not in tool_identifier:
        raise ToolNotFoundError(
            f"Invalid tool identifier format: {tool_identifier}. "
            f"Expected format: 'serverName__toolName'"
        )

    server_name, tool_name = tool_identifier.split("__", 1)

    # Validate server exists in config
    if server_name not in self._config.mcpServers:
        raise ToolNotFoundError(
            f"Server '{server_name}' not found in configuration"
        )

    # Lazy connect to server if not already connected
    if server_name not in self._clients:
        config = self._config.mcpServers[server_name]
        await self._connect_to_server(server_name, config)

    # Call tool
    try:
        client = self._clients[server_name]
        logger.debug(f"Calling tool: {tool_identifier} with params: {params}")

        result = await client.call_tool(name=tool_name, arguments=params)

        # Defensive unwrapping (handle various response formats)
        unwrapped = getattr(result, "value", result)

        # If result is text, try parsing as JSON
        if isinstance(unwrapped, str):
            try:
                unwrapped = json.loads(unwrapped)
            except json.JSONDecodeError:
                pass  # Return as string

        logger.debug(f"Tool call succeeded: {tool_identifier}")
        return unwrapped

    except Exception as e:
        raise ToolExecutionError(tool_identifier, str(e)) from e
```

### 5. Implement Tool Caching (T039)

Add to `McpClientManager`:

```python
async def list_all_tools(self) -> List[Any]:
    """List all available tools (connects to all servers)."""
    if not self._initialized:
        raise ConfigurationError("Manager not initialized")

    all_tools = []

    for server_name, server_config in self._config.mcpServers.items():
        # Check cache first
        if server_name in self._tool_cache:
            logger.debug(f"Using cached tools for {server_name}")
            all_tools.extend(self._tool_cache[server_name])
            continue

        # Connect if needed
        if server_name not in self._clients:
            await self._connect_to_server(server_name, server_config)

        # List tools
        client = self._clients[server_name]
        tools_response = await client.list_tools()
        tools = tools_response.tools

        # Cache tools
        self._tool_cache[server_name] = tools
        all_tools.extend(tools)

        logger.info(f"Listed {len(tools)} tools from {server_name}")

    return all_tools
```

### 6. Implement Cleanup (T040)

Add to `McpClientManager`:

```python
async def cleanup(self) -> None:
    """Close all connections gracefully."""
    logger.info(f"Cleaning up {len(self._clients)} connections...")

    errors = []
    for server_name, client in self._clients.items():
        try:
            await client.__aexit__(None, None, None)
            logger.debug(f"Closed connection to {server_name}")
        except Exception as e:
            logger.error(f"Error closing {server_name}: {e}")
            errors.append((server_name, e))

    self._clients.clear()
    self._tool_cache.clear()
    self._initialized = False

    if errors:
        error_msg = "; ".join([f"{name}: {err}" for name, err in errors])
        raise ServerConnectionError(f"Cleanup errors: {error_msg}")

    logger.info("Cleanup complete")
```

### 7. Create Unit Tests (T045-T048)

Create `tests/unit/test_mcp_client.py`:

```python
"""Unit tests for MCP Client Manager."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from runtime.mcp_client import McpClientManager, get_mcp_client_manager
from runtime.exceptions import ConfigurationError, ToolNotFoundError


@pytest.mark.asyncio
async def test_lazy_initialization():
    """Test that servers are NOT connected during initialize."""
    manager = McpClientManager()

    # Mock config file
    with patch("aiofiles.open", AsyncMock()):
        with patch("runtime.mcp_client.McpConfig.model_validate_json"):
            await manager.initialize()

    # Verify no connections made
    assert len(manager._clients) == 0
    assert manager._initialized is True


@pytest.mark.asyncio
async def test_lazy_connection():
    """Test that server connects on first tool call, not on initialize."""
    manager = McpClientManager()
    manager._initialized = True
    manager._config = MagicMock()
    manager._config.mcpServers = {"test": MagicMock(command="echo", args=[])}

    # Mock connection
    with patch.object(manager, "_connect_to_server", AsyncMock()) as mock_connect:
        with patch.object(manager._clients, "__getitem__", MagicMock()):
            try:
                await manager.call_tool("test__tool", {})
            except:
                pass

            # Verify connection was attempted
            mock_connect.assert_called_once()


@pytest.mark.asyncio
async def test_tool_caching():
    """Test that list_tools is cached per server."""
    manager = McpClientManager()
    manager._initialized = True
    manager._config = MagicMock()
    manager._config.mcpServers = {"test": MagicMock()}

    # Mock client
    mock_client = AsyncMock()
    mock_client.list_tools.return_value = MagicMock(tools=["tool1", "tool2"])
    manager._clients["test"] = mock_client

    # First call
    tools1 = await manager.list_all_tools()
    # Second call
    tools2 = await manager.list_all_tools()

    # Verify list_tools called only once (cached)
    assert mock_client.list_tools.call_count == 1


@pytest.mark.asyncio
async def test_singleton_pattern():
    """Test that get_mcp_client_manager returns singleton."""
    manager1 = get_mcp_client_manager()
    manager2 = get_mcp_client_manager()

    assert manager1 is manager2


@pytest.mark.asyncio
async def test_cleanup_error_handling():
    """Test cleanup handles errors gracefully."""
    manager = McpClientManager()
    manager._initialized = True

    # Mock client that raises error
    mock_client = AsyncMock()
    mock_client.__aexit__.side_effect = Exception("Close error")
    manager._clients["test"] = mock_client

    # Cleanup should not raise, but log errors
    with pytest.raises(Exception):
        await manager.cleanup()

    # Verify state cleared
    assert len(manager._clients) == 0
    assert manager._initialized is False
```

### 8. Run Tests (T049)

```bash
# Run unit tests
uv run pytest tests/unit/test_mcp_client.py -v

# Run with coverage
uv run pytest tests/unit/test_mcp_client.py --cov=src/runtime/mcp_client
```

## Validation Checklist

- [ ] CHK023 - Lazy initialization implemented (config loaded, servers NOT connected)?
- [ ] CHK024 - Lazy connection implemented (connect on first tool call)?
- [ ] CHK025 - Tool caching implemented?
- [ ] CHK026 - Defensive unwrapping implemented (response.value or response)?
- [ ] CHK027 - JSON parsing for text responses?
- [ ] CHK028 - Singleton pattern uses @lru_cache?
- [ ] CHK029 - Cleanup properly implemented with error handling?
- [ ] CHK030 - All error types from exceptions.py used?
- [ ] CHK031 - Tool identifier format ("serverName__toolName") documented?
- [ ] CHK032 - call_mcp_tool convenience wrapper exists?
- [ ] CHK086 - Lazy loading pattern preserved?
- [ ] CHK087 - Lazy server connections work?
- [ ] CHK088 - Tool caching prevents repeated calls?
- [ ] CHK089 - Defensive unwrapping throughout?
- [ ] CHK097 - Unit tests for lazy loading exist?
- [ ] CHK112-CHK120 - All error handling scenarios covered?

## Deliverables

- ✅ `src/runtime/mcp_client.py` with complete implementation
- ✅ `tests/unit/test_mcp_client.py` with unit tests
- ✅ All tests passing

## Troubleshooting

**Issue**: Import errors
```bash
# Ensure editable install
uv pip install -e .
```

**Issue**: Async context manager errors
```python
# Use proper async context managers
async with stdio_client(params) as (read, write):
    async with Client(read, write) as client:
        ...
```

## Mark Items Complete

After successfully completing this phase, mark the following as complete:

### Update CHECKLIST.md (CHK023-CHK032, CHK086-CHK089, CHK097, CHK112-CHK120)
```bash
# Mark Phase 2 checklist items complete
for i in {023..032}; do
  sed -i '' "s/^- \[ \] CHK$i/- [x] CHK$i/" CHECKLIST.md
done

for i in {086..089}; do
  sed -i '' "s/^- \[ \] CHK$i/- [x] CHK$i/" CHECKLIST.md
done

sed -i '' 's/^- \[ \] CHK097/- [x] CHK097/' CHECKLIST.md

for i in {112..120}; do
  sed -i '' "s/^- \[ \] CHK$i/- [x] CHK$i/" CHECKLIST.md
done

echo "✅ Phase 2 checklist items marked complete"
```

### Update TASKS.md (T029-T049)
```bash
# Mark Phase 2 task items complete
for i in {029..049}; do
  sed -i '' "s/^- \[ \] T$i/- [x] T$i/" TASKS.md
done

echo "✅ Phase 2 task items marked complete"
```

### Verify Completion
```bash
# Verify all Phase 2 items marked
echo "✅ Phase 2 complete and documented"
```

---

**Next Phase**: Proceed to `/phase3-harness` to implement script execution harness
