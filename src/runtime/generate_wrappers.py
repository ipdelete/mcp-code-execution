"""
Generate typed Python wrappers from MCP server tool definitions.

This module implements the progressive disclosure pattern by generating
Pydantic models and wrapper functions for each MCP tool.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List

from .config import McpConfig
from .schema_utils import (
    generate_pydantic_model,
    json_schema_to_python_type,
    sanitize_name,
)

logger = logging.getLogger("mcp_execution.generate_wrappers")


def generate_tool_wrapper(
    server_name: str, tool_name: str, tool: Any
) -> str:
    """
    Generate Python wrapper function for a tool.

    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool
        tool: Tool definition from MCP

    Returns:
        Python code for wrapper function

    Example output:
        ```python
        async def git_status(params: GitStatusParams) -> Dict[str, Any]:
            '''Get git repository status'''
            from runtime.mcp_client import call_mcp_tool
            from runtime.normalize_fields import normalize_field_names

            result = await call_mcp_tool("git__git_status", params.model_dump())
            normalized = normalize_field_names(result, "git")
            return GitStatusResult.model_validate(normalized)
        ```
    """
    safe_tool_name = sanitize_name(tool_name)
    tool_identifier = f"{server_name}__{tool_name}"

    # Get tool description
    description = getattr(tool, "description", "MCP tool wrapper")
    description_escaped = description.replace('"""', '\\"\\"\\"')

    # Generate parameter model name
    params_model = f"{safe_tool_name.title().replace('_', '')}Params"

    # Generate wrapper function
    wrapper = f'''
async def {safe_tool_name}(params: {params_model}) -> Dict[str, Any]:
    """
    {description_escaped}

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("{tool_identifier}", params.model_dump(exclude_none=True))

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "{server_name}")

    return normalized
'''

    return wrapper


def generate_params_model(tool_name: str, tool: Any) -> str:
    """
    Generate Pydantic model for tool parameters.

    Args:
        tool_name: Name of the tool
        tool: Tool definition from MCP

    Returns:
        Python code for Pydantic params model
    """
    safe_tool_name = sanitize_name(tool_name)
    model_name = f"{safe_tool_name.title().replace('_', '')}Params"

    # Get input schema
    input_schema = getattr(tool, "inputSchema", {})

    if not input_schema or input_schema.get("type") != "object":
        # No parameters
        return f'''
class {model_name}(BaseModel):
    """Parameters for {tool_name}."""
    pass
'''

    description = f"Parameters for {tool_name}"
    return generate_pydantic_model(model_name, input_schema, description)


def generate_server_module(
    server_name: str, tools: List[Any], output_dir: Path
) -> None:
    """
    Generate complete module for a server's tools.

    Creates:
    - Individual tool files (servers/{server_name}/{tool_name}.py)
    - Barrel export (__init__.py)
    - README.md

    Args:
        server_name: Name of the MCP server
        tools: List of tool definitions
        output_dir: Output directory (src/servers/)
    """
    server_dir = output_dir / server_name
    server_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating wrappers for server: {server_name} ({len(tools)} tools)")

    imports = [
        "from typing import Any, Dict, List, Optional",
        "from pydantic import BaseModel, Field",
        "from typing import Literal",
    ]

    tool_names = []

    for tool in tools:
        tool_name = sanitize_name(tool.name)
        tool_names.append(tool_name)

        # Generate tool file
        tool_file = server_dir / f"{tool_name}.py"

        # Generate models and wrapper
        params_model = generate_params_model(tool.name, tool)
        wrapper_func = generate_tool_wrapper(server_name, tool.name, tool)

        # Write tool file
        tool_code = "\n".join(imports) + "\n\n" + params_model + "\n" + wrapper_func

        tool_file.write_text(tool_code)
        logger.debug(f"Generated: {tool_file}")

    # Generate __init__.py (barrel export)
    init_file = server_dir / "__init__.py"
    init_imports = [f"from .{name} import {name}" for name in tool_names]
    init_all = f"__all__ = {tool_names}"
    init_content = "\n".join(init_imports) + "\n\n" + init_all
    init_file.write_text(init_content)

    # Generate README.md
    readme_file = server_dir / "README.md"
    readme_content = f"""# {server_name} MCP Tools

Auto-generated wrappers for {server_name} MCP server.

## Tools

{chr(10).join([f"- `{tool.name}`: {getattr(tool, 'description', 'No description')}" for tool in tools])}

## Usage

```python
from servers.{server_name} import {tool_names[0] if tool_names else 'tool_name'}

# Use the tool
result = await {tool_names[0] if tool_names else 'tool_name'}(params)
```

**Note**: This file is auto-generated. Do not edit manually.
"""
    readme_file.write_text(readme_content)


async def generate_wrappers(config_path: Path | None = None) -> None:
    """
    Main wrapper generation orchestrator.

    1. Load mcp_config.json
    2. For each server:
       a. Connect and list tools
       b. Generate wrappers
       c. Write to src/servers/{server}/
    3. Generate top-level __init__.py

    Args:
        config_path: Path to mcp_config.json
    """
    logger.info("Starting wrapper generation...")

    # Load config
    config_file = config_path or Path.cwd() / "mcp_config.json"
    if not config_file.exists():
        logger.error(f"Config file not found: {config_file}")
        return

    import aiofiles
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async with aiofiles.open(config_file, "r") as f:
        content = await f.read()
    config = McpConfig.model_validate_json(content)

    # Output directory
    output_dir = Path(__file__).parent.parent.parent / "servers"
    output_dir.mkdir(exist_ok=True)

    # Generate for each server
    for server_name, server_config in config.mcpServers.items():
        try:
            logger.info(f"Connecting to server: {server_name}")

            # Create stdio server parameters
            server_params = StdioServerParameters(
                command=server_config.command,
                args=server_config.args,
                env=server_config.env,
            )

            # Connect and list tools using proper context manager pattern
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # List tools
                    tools_response = await session.list_tools()
                    tools = tools_response.tools
                    logger.info(f"Found {len(tools)} tools for {server_name}")

                    # Generate wrappers
                    generate_server_module(server_name, tools, output_dir)

        except Exception as e:
            logger.error(f"Failed to generate wrappers for {server_name}: {e}")
            import traceback
            traceback.print_exc()

    logger.info("Wrapper generation complete!")


def main() -> None:
    """CLI entry point."""
    asyncio.run(generate_wrappers())


if __name__ == "__main__":
    main()
