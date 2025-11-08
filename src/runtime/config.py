"""Configuration models using Pydantic for MCP Code Execution runtime.

This module defines the configuration structure for MCP servers and provides
validation using Pydantic models.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ServerConfig(BaseModel):
    """Configuration for a single MCP server.

    Attributes:
        command: The command to execute (e.g., "npx", "python")
        args: List of arguments to pass to the command
        env: Optional environment variables for the server process
        disabled: Whether this server should be skipped (default: False)
    """

    command: str = Field(..., description="Command to execute the MCP server")
    args: list[str] = Field(default_factory=list, description="Arguments for the command")
    env: dict[str, str] | None = Field(
        default=None, description="Environment variables for the server"
    )
    disabled: bool = Field(default=False, description="Whether to skip this server")

    @field_validator("command")
    @classmethod
    def command_not_empty(cls, v: str) -> str:
        """Validate that command is not empty."""
        if not v or not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip()

    @field_validator("args")
    @classmethod
    def args_not_none(cls, v: list[str]) -> list[str]:
        """Ensure args is a list, even if None."""
        return v if v is not None else []


class McpConfig(BaseModel):
    """Root configuration for all MCP servers.

    Attributes:
        mcpServers: Dictionary mapping server names to their configurations
    """

    mcpServers: dict[str, ServerConfig] = Field(
        ..., description="Mapping of server names to configurations"
    )

    @field_validator("mcpServers")
    @classmethod
    def servers_not_empty(cls, v: dict[str, ServerConfig]) -> dict[str, ServerConfig]:
        """Validate that at least one server is configured."""
        if not v:
            raise ValueError("At least one MCP server must be configured")
        return v

    def get_enabled_servers(self) -> dict[str, ServerConfig]:
        """Return only enabled servers.

        Returns:
            Dictionary of server names to configurations for enabled servers only
        """
        return {name: config for name, config in self.mcpServers.items() if not config.disabled}

    def get_server(self, name: str) -> ServerConfig | None:
        """Get configuration for a specific server by name.

        Args:
            name: Server name to look up

        Returns:
            ServerConfig if found, None otherwise
        """
        return self.mcpServers.get(name)

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "McpConfig":
        """Create McpConfig from a dictionary.

        Args:
            config_dict: Dictionary containing configuration data

        Returns:
            Validated McpConfig instance

        Raises:
            ValidationError: If configuration is invalid
        """
        return cls.model_validate(config_dict)

    @classmethod
    def from_json(cls, json_str: str) -> "McpConfig":
        """Create McpConfig from a JSON string.

        Args:
            json_str: JSON string containing configuration

        Returns:
            Validated McpConfig instance

        Raises:
            ValidationError: If configuration is invalid
            JSONDecodeError: If JSON is malformed
        """
        return cls.model_validate_json(json_str)
