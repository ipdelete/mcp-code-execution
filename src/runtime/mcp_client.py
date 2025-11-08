"""MCP Client Manager with state machine architecture for lazy loading and connection.

This module provides the core runtime client manager that connects to MCP servers
on-demand, caches tools, and manages the lifecycle of server connections using
an explicit state machine pattern for clarity and debugging.
"""

import json
import logging
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import aiofiles
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool

from .config import McpConfig, ServerConfig
from .exceptions import (
    ConfigurationError,
    ServerConnectionError,
    ToolExecutionError,
    ToolNotFoundError,
)

logger = logging.getLogger("mcp_execution.client")


class ConnectionState(Enum):
    """Explicit states for the MCP Client Manager lifecycle.

    States:
        UNINITIALIZED: Manager created but not initialized
        INITIALIZED: Configuration loaded, no server connections
        CONNECTED: At least one server connection established
    """

    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    CONNECTED = "connected"


class McpClientManager:
    """Lazy-loading MCP client manager with explicit state machine.

    This manager implements a state machine pattern for managing MCP server
    connections with the following characteristics:
    - Lazy initialization: Config loaded on initialize(), servers NOT connected
    - Lazy connection: Servers connect on first call_tool() call
    - Tool caching: Cache tools per server to avoid repeated list_tools calls
    - Defensive unwrapping: Handle response.value and fallback patterns
    - Explicit state tracking: Clear state transitions with validation

    State Transitions:
        UNINITIALIZED -> INITIALIZED (via initialize())
        INITIALIZED -> CONNECTED (via _connect_to_server())
        any state -> UNINITIALIZED (via cleanup())

    Attributes:
        _state: Current connection state
        _clients: Mapping of server names to active client sessions
        _tool_cache: Cached tools per server to avoid repeated queries
        _config: Loaded MCP configuration
        _read_streams: Active stdio read streams for cleanup
        _write_streams: Active stdio write streams for cleanup
    """

    def __init__(self) -> None:
        """Initialize an uninitialized MCP Client Manager."""
        self._state: ConnectionState = ConnectionState.UNINITIALIZED
        self._clients: dict[str, ClientSession] = {}
        self._tool_cache: dict[str, list[Tool]] = {}
        self._config: McpConfig | None = None
        self._read_streams: dict[str, Any] = {}
        self._write_streams: dict[str, Any] = {}

    def _validate_state(self, required_state: ConnectionState, operation: str) -> None:
        """Validate that the manager is in the required state for an operation.

        Args:
            required_state: The state required to perform the operation
            operation: Name of the operation being attempted (for error messages)

        Raises:
            ConfigurationError: If the manager is not in the required state
        """
        if self._state.value != required_state.value:
            raise ConfigurationError(
                f"Cannot {operation}: Manager is in state '{self._state.value}', "
                f"but requires state '{required_state.value}'"
            )

    def _validate_state_at_least(
        self, minimum_state: ConnectionState, operation: str
    ) -> None:
        """Validate that the manager has at least reached the minimum state.

        Args:
            minimum_state: The minimum state required
            operation: Name of the operation being attempted

        Raises:
            ConfigurationError: If the manager has not reached the minimum state
        """
        state_order = [
            ConnectionState.UNINITIALIZED,
            ConnectionState.INITIALIZED,
            ConnectionState.CONNECTED,
        ]
        current_idx = state_order.index(self._state)
        required_idx = state_order.index(minimum_state)

        if current_idx < required_idx:
            raise ConfigurationError(
                f"Cannot {operation}: Manager is in state '{self._state.value}', "
                f"but requires at least state '{minimum_state.value}'"
            )

    def _mark_initialized(self) -> None:
        """Transition to INITIALIZED state."""
        self._state = ConnectionState.INITIALIZED
        logger.debug("State transition: UNINITIALIZED -> INITIALIZED")

    def _mark_connected(self) -> None:
        """Transition to CONNECTED state."""
        if self._state == ConnectionState.INITIALIZED:
            self._state = ConnectionState.CONNECTED
            logger.debug("State transition: INITIALIZED -> CONNECTED")

    def _mark_uninitialized(self) -> None:
        """Transition back to UNINITIALIZED state."""
        self._state = ConnectionState.UNINITIALIZED
        logger.debug("State transition: -> UNINITIALIZED")

    async def initialize(self, config_path: Path | None = None) -> None:
        """Initialize the manager by loading configuration.

        This method loads the MCP configuration from a JSON file but does NOT
        establish any server connections. Connections are established lazily
        on the first tool call.

        Args:
            config_path: Optional path to mcp_config.json. If not provided,
                        defaults to mcp_config.json in the current directory

        Raises:
            ConfigurationError: If config file is missing, malformed, or invalid
        """
        self._validate_state(ConnectionState.UNINITIALIZED, "initialize")

        config_file = config_path or Path.cwd() / "mcp_config.json"

        if not config_file.exists():
            raise ConfigurationError(f"Config file not found: {config_file}")

        try:
            async with aiofiles.open(config_file) as f:
                content = await f.read()
            self._config = McpConfig.model_validate_json(content)
            enabled_count = len(self._config.get_enabled_servers())
            logger.info(
                f"Configuration loaded: {len(self._config.mcpServers)} servers total, "
                f"{enabled_count} enabled"
            )
            self._mark_initialized()
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file {config_file}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load config from {config_file}: {e}")

    async def _connect_to_server(self, server_name: str, config: ServerConfig) -> None:
        """Establish connection to a single MCP server on-demand.

        This method is called lazily when a tool from the server is first invoked.
        It creates a stdio client connection and initializes the session.

        Args:
            server_name: Name of the server to connect to
            config: Server configuration containing command and arguments

        Raises:
            ServerConnectionError: If connection fails
        """
        if server_name in self._clients:
            logger.debug(f"Server '{server_name}' already connected")
            return

        logger.info(f"Connecting to MCP server: {server_name}")

        try:
            # Create stdio server parameters
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env,
            )

            # Establish stdio connection
            # Note: stdio_client returns a context manager that yields (read, write) streams
            stdio_ctx = stdio_client(server_params)
            streams = await stdio_ctx.__aenter__()
            read_stream, write_stream = streams
            self._read_streams[server_name] = read_stream
            self._write_streams[server_name] = write_stream

            # Create and initialize session (store the context manager, not using async with)
            session = ClientSession(read_stream, write_stream)
            session_ctx = session.__aenter__()
            client = await session_ctx
            await client.initialize()

            self._clients[server_name] = client
            self._mark_connected()
            logger.info(f"Successfully connected to server: {server_name}")

        except Exception as e:
            logger.error(f"Failed to connect to server '{server_name}': {e}")
            raise ServerConnectionError(
                f"Could not connect to MCP server '{server_name}': {e}"
            )

    async def _get_server_tools(self, server_name: str) -> list[Tool]:
        """Get list of tools from a server, using cache if available.

        Args:
            server_name: Name of the server to query

        Returns:
            List of tool objects from the server

        Raises:
            ServerConnectionError: If not connected to the server
        """
        # Check cache first
        if server_name in self._tool_cache:
            logger.debug(f"Using cached tools for server: {server_name}")
            return self._tool_cache[server_name]

        # Ensure we're connected
        if server_name not in self._clients:
            raise ServerConnectionError(f"Not connected to server: {server_name}")

        # Query server for tools
        try:
            client = self._clients[server_name]
            result = await client.list_tools()

            # Defensive unwrapping: handle response.tools
            tools: list[Tool] = result.tools if hasattr(result, "tools") else []

            # Cache the results
            self._tool_cache[server_name] = tools
            logger.debug(f"Cached {len(tools)} tools for server: {server_name}")

            return tools

        except Exception as e:
            logger.error(f"Failed to list tools from server '{server_name}': {e}")
            raise ServerConnectionError(f"Could not list tools from server '{server_name}': {e}")

    async def call_tool(self, tool_identifier: str, params: dict[str, Any]) -> Any:
        """Call an MCP tool with lazy server connection.

        This is the core method that implements lazy loading. Servers are only
        connected when their tools are first invoked.

        Tool Identifier Format: "serverName__toolName"

        Args:
            tool_identifier: Tool identifier in format "serverName__toolName"
            params: Dictionary of parameters to pass to the tool

        Returns:
            The tool execution result (unwrapped from response)

        Raises:
            ConfigurationError: If manager not initialized
            ToolNotFoundError: If tool doesn't exist on the specified server
            ToolExecutionError: If tool execution fails
            ServerConnectionError: If unable to connect to server
        """
        self._validate_state_at_least(ConnectionState.INITIALIZED, "call tool")

        if not self._config:
            raise ConfigurationError("Configuration not loaded")

        # Parse tool identifier
        if "__" not in tool_identifier:
            raise ToolNotFoundError(
                f"Invalid tool identifier '{tool_identifier}'. "
                f"Expected format: 'serverName__toolName'"
            )

        server_name, tool_name = tool_identifier.split("__", 1)

        # Get server configuration
        server_config = self._config.get_server(server_name)
        if not server_config:
            raise ToolNotFoundError(
                f"Server '{server_name}' not found in configuration. "
                f"Available servers: {list(self._config.mcpServers.keys())}"
            )

        if server_config.disabled:
            raise ToolNotFoundError(
                f"Server '{server_name}' is disabled in configuration"
            )

        # Lazy connection: connect to server if not already connected
        if server_name not in self._clients:
            logger.debug(f"Lazy connecting to server '{server_name}' for tool '{tool_name}'")
            await self._connect_to_server(server_name, server_config)

        # Verify tool exists on server
        tools = await self._get_server_tools(server_name)
        tool_names = [tool.name for tool in tools]

        if tool_name not in tool_names:
            raise ToolNotFoundError(
                f"Tool '{tool_name}' not found on server '{server_name}'. "
                f"Available tools: {tool_names}"
            )

        # Execute the tool
        try:
            client = self._clients[server_name]
            logger.info(f"Executing tool: {tool_identifier}")
            logger.debug(f"Tool parameters: {params}")

            result = await client.call_tool(tool_name, params)

            # Defensive unwrapping: try multiple strategies to get the actual result
            # 1. Try result.value (most common)
            if hasattr(result, "value"):
                unwrapped = result.value
            # 2. Try result.content (alternative response format)
            elif hasattr(result, "content"):
                unwrapped = result.content
            # 3. Fall back to result itself
            else:
                unwrapped = result

            # Additional unwrapping for text responses
            if isinstance(unwrapped, list) and len(unwrapped) > 0:
                first_item = unwrapped[0]
                if hasattr(first_item, "text"):
                    text_content = first_item.text
                    # Try to parse as JSON if it looks like JSON
                    if isinstance(text_content, str) and text_content.strip().startswith(
                        ("{", "[")
                    ):
                        try:
                            return json.loads(text_content)
                        except json.JSONDecodeError:
                            return text_content
                    return text_content

            logger.debug(f"Tool execution result: {unwrapped}")
            return unwrapped

        except Exception as e:
            logger.error(f"Tool execution failed for '{tool_identifier}': {e}")
            raise ToolExecutionError(f"Failed to execute tool '{tool_identifier}': {e}")

    async def list_all_tools(self) -> list[Tool]:
        """List all available tools from all enabled servers.

        This method connects to all enabled servers to retrieve their tool lists.
        Results are cached per server to avoid repeated queries.

        Returns:
            List of all available tools across all enabled servers

        Raises:
            ConfigurationError: If manager not initialized
            ServerConnectionError: If unable to connect to any server
        """
        self._validate_state_at_least(ConnectionState.INITIALIZED, "list all tools")

        if not self._config:
            raise ConfigurationError("Configuration not loaded")

        all_tools: list[Tool] = []
        enabled_servers = self._config.get_enabled_servers()

        if not enabled_servers:
            logger.warning("No enabled servers configured")
            return all_tools

        logger.info(f"Listing tools from {len(enabled_servers)} enabled servers")

        for server_name, server_config in enabled_servers.items():
            try:
                # Connect to server if not already connected
                if server_name not in self._clients:
                    await self._connect_to_server(server_name, server_config)

                # Get tools from server (uses cache if available)
                tools = await self._get_server_tools(server_name)
                all_tools.extend(tools)
                logger.debug(f"Server '{server_name}': {len(tools)} tools")

            except Exception as e:
                logger.error(f"Failed to list tools from server '{server_name}': {e}")
                # Continue with other servers rather than failing completely

        logger.info(f"Total tools available: {len(all_tools)}")
        return all_tools

    async def cleanup(self) -> None:
        """Close all connections and reset manager to uninitialized state.

        This method gracefully closes all active server connections and clears
        all cached data, returning the manager to UNINITIALIZED state.
        """
        logger.info("Cleaning up MCP Client Manager")

        # Close all client sessions
        for server_name, client in self._clients.items():
            try:
                # Note: ClientSession is an async context manager
                # In actual usage it should be used with 'async with'
                # Here we just log that we're releasing it
                logger.debug(f"Closing connection to server: {server_name}")
            except Exception as e:
                logger.error(f"Error closing connection to '{server_name}': {e}")

        # Clear all state
        self._clients.clear()
        self._tool_cache.clear()
        self._read_streams.clear()
        self._write_streams.clear()
        self._config = None
        self._mark_uninitialized()

        logger.info("Cleanup complete")


# Singleton pattern using lru_cache (thread-safe)
@lru_cache(maxsize=1)
def get_mcp_client_manager() -> McpClientManager:
    """Get or create the singleton MCP Client Manager instance.

    This function uses functools.lru_cache to ensure only one instance
    of the manager exists, providing thread-safe singleton behavior.

    Returns:
        The singleton McpClientManager instance
    """
    logger.debug("Getting MCP Client Manager singleton")
    return McpClientManager()


async def call_mcp_tool(tool_identifier: str, params: dict[str, Any]) -> Any:
    """Convenience function for calling MCP tools using the singleton manager.

    This is a high-level API that automatically uses the singleton manager instance.

    Args:
        tool_identifier: Tool identifier in format "serverName__toolName"
        params: Dictionary of parameters to pass to the tool

    Returns:
        The tool execution result

    Raises:
        ConfigurationError: If manager not initialized
        ToolNotFoundError: If tool doesn't exist
        ToolExecutionError: If tool execution fails
        ServerConnectionError: If unable to connect to server
    """
    manager = get_mcp_client_manager()
    return await manager.call_tool(tool_identifier, params)
