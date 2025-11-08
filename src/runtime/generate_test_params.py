"""
Generate test parameters for MCP tools using Claude LLM.

This module uses Claude to generate reasonable test parameters from tool
inputSchemas, enabling automatic discovery configuration generation.
It also classifies tools by safety (SAFE/DANGEROUS/UNKNOWN) based on patterns
and descriptions.
"""

import json
import logging
import re
from enum import Enum
from typing import Any

try:
    import anthropic
except ImportError:
    anthropic = None

logger = logging.getLogger("mcp_execution.generate_test_params")


class ToolSafety(str, Enum):
    """Safety classification for tools."""

    SAFE = "safe"
    DANGEROUS = "dangerous"
    UNKNOWN = "unknown"


# Regex patterns for tool classification
SAFE_PATTERNS = [
    r"^get_",
    r"^list_",
    r"^search_",
    r"^describe_",
    r"^fetch",
    r"^read_",
    r"^show_",
    r"^view_",
    r"^find_",
    r"^query_",
]

DANGEROUS_PATTERNS = [
    r"^delete_",
    r"^remove_",
    r"^drop_",
    r"^destroy_",
    r"^kill_",
    r"^create_.*table",
    r"^update_",
    r"^write_",
    r"^execute_",
    r"^run_",
    r"^modify_",
    r"^set_",
    r"^put_",
    r"^post_",
]

SAFE_KEYWORDS = [
    "get",
    "list",
    "read",
    "fetch",
    "search",
    "query",
    "show",
    "view",
    "find",
    "describe",
]

DANGEROUS_KEYWORDS = [
    "delete",
    "remove",
    "drop",
    "destroy",
    "kill",
    "update",
    "write",
    "execute",
    "modify",
    "truncate",
]


def classify_tool(tool_name: str, description: str | None = None) -> ToolSafety:
    """
    Classify a tool as SAFE, DANGEROUS, or UNKNOWN based on patterns and description.

    Classification strategy:
    1. Check description for dangerous keywords (overrides all else)
    2. Check against explicit regex patterns
    3. Fall back to description keywords
    4. Default to UNKNOWN if no signals

    Args:
        tool_name: Name of the tool
        description: Optional tool description

    Returns:
        ToolSafety classification
    """
    # First priority: dangerous keywords in description override everything
    if description:
        desc_lower = description.lower()
        if any(kw in desc_lower for kw in DANGEROUS_KEYWORDS):
            return ToolSafety.DANGEROUS

    # Check dangerous patterns (high priority)
    if any(re.match(pattern, tool_name, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS):
        return ToolSafety.DANGEROUS

    # Check safe patterns
    if any(re.match(pattern, tool_name, re.IGNORECASE) for pattern in SAFE_PATTERNS):
        return ToolSafety.SAFE

    # Fall back to description safe keywords
    if description:
        desc_lower = description.lower()
        if any(kw in desc_lower for kw in SAFE_KEYWORDS):
            return ToolSafety.SAFE

    return ToolSafety.UNKNOWN


def generate_test_parameters(
    tool_name: str,
    input_schema: dict[str, Any],
    description: str | None = None,
) -> dict[str, Any] | None:
    """
    Generate test parameters for a tool using Claude.

    Uses Claude Haiku to generate minimal but valid test parameters that
    satisfy the tool's inputSchema. Returns None on any error (safe fallback).

    Args:
        tool_name: Name of the tool
        input_schema: JSON Schema for tool inputs
        description: Optional tool description for context

    Returns:
        Dict of test parameters, or None if generation fails

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "repo_path": {"type": "string"},
        ...         "max_count": {"type": "integer"}
        ...     },
        ...     "required": ["repo_path"]
        ... }
        >>> params = generate_test_parameters("git_log", schema)
        >>> # Returns: {"repo_path": ".", "max_count": 1}
    """
    if anthropic is None:
        logger.warning("anthropic library not installed. " "Install with: uv pip install anthropic")
        return None

    try:
        client = anthropic.Anthropic()

        prompt = f"""Generate minimal test parameters for this MCP tool.

Tool: {tool_name}
{f'Description: {description}' if description else ''}

Input Schema:
```json
{json.dumps(input_schema, indent=2)}
```

Requirements:
- Return ONLY valid JSON that satisfies the schema
- Use minimal values: empty strings, 0, 1, [], {{}}
- Be conservative: avoid URLs, file paths, or special values unless required
- Ensure all required fields are present
- For arrays/objects, use minimal examples (1-2 items)

Return ONLY the JSON object, no explanation."""

        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract JSON from response
        response_text = message.content[0].text if message.content else ""
        response_text = response_text.strip()

        # Handle markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        params = json.loads(response_text)

        if not isinstance(params, dict):
            logger.warning(f"Generated params for {tool_name} is not a dict: {type(params)}")
            return None

        logger.debug(f"Generated params for {tool_name}: {params}")
        return params

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse generated params for {tool_name}: {e}")
        return None
    except anthropic.APIError as e:
        logger.warning(f"Anthropic API error generating params for {tool_name}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error generating params for {tool_name}: {e}")
        return None


def build_discovery_config(
    servers_tools: dict[str, list[dict[str, Any]]],
    skip_dangerous: bool = True,
) -> dict[str, Any]:
    """
    Build a discovery config from servers and their tools.

    For each tool, generates test parameters and classifies by safety.
    Tools marked as DANGEROUS are excluded by default.

    Args:
        servers_tools: Dict mapping server names to list of tool definitions
                      Each tool should have: name, inputSchema, description
        skip_dangerous: If True, exclude DANGEROUS tools from config (default: True)

    Returns:
        Dictionary suitable for writing to discovery_config.json

    Example output:
        {
            "servers": {
                "git": {
                    "safeTools": {
                        "git_log": {"repo_path": ".", "max_count": 1},
                        "git_status": {"repo_path": "."}
                    }
                }
            },
            "metadata": {
                "generated": true,
                "tools_skipped": {"dangerous": [...], "unknown": [...]},
                "generated_count": 5,
                "skipped_count": 2
            }
        }
    """
    config: dict[str, Any] = {"servers": {}}
    tools_skipped: dict[str, list[str]] = {"dangerous": [], "unknown": []}
    metadata: dict[str, Any] = {
        "generated": True,
        "tools_skipped": tools_skipped,
        "generated_count": 0,
        "skipped_count": 0,
    }

    for server_name, tools in servers_tools.items():
        safe_tools_config: dict[str, dict[str, Any]] = {}
        generated_count = 0
        skipped_count = 0

        for tool in tools:
            tool_name = tool.get("name", "")
            if not tool_name:
                continue

            description = tool.get("description", "")
            input_schema = tool.get("inputSchema", {})

            # Classify tool
            safety = classify_tool(tool_name, description)

            # Skip dangerous tools if requested
            if skip_dangerous and safety == ToolSafety.DANGEROUS:
                tools_skipped["dangerous"].append(tool_name)
                skipped_count += 1
                continue

            # Skip unknown tools (require manual config)
            if safety == ToolSafety.UNKNOWN:
                tools_skipped["unknown"].append(tool_name)
                skipped_count += 1
                continue

            # Generate test parameters
            params = generate_test_parameters(tool_name, input_schema, description)
            if params is None:
                logger.warning(f"Failed to generate params for {server_name}.{tool_name}")
                tools_skipped["unknown"].append(tool_name)
                skipped_count += 1
                continue

            safe_tools_config[tool_name] = params
            generated_count += 1

        if safe_tools_config:
            config["servers"][server_name] = {"safeTools": safe_tools_config}

        metadata["generated_count"] = metadata["generated_count"] + generated_count
        metadata["skipped_count"] = metadata["skipped_count"] + skipped_count

    config["metadata"] = metadata
    return config


def print_discovery_summary(config: dict[str, Any]) -> None:
    """
    Print a human-readable summary of generated discovery config.

    Args:
        config: Discovery configuration dictionary
    """
    metadata = config.get("metadata", {})
    servers = config.get("servers", {})

    print("\n" + "=" * 60)
    print("DISCOVERY CONFIG GENERATION SUMMARY")
    print("=" * 60)

    print(f"\n✓ Generated:  {metadata.get('generated_count', 0)} tools")
    print(f"⊗ Skipped:    {metadata.get('skipped_count', 0)} tools")

    skipped = metadata.get("tools_skipped", {})
    if skipped.get("dangerous"):
        print(f"  - Dangerous: {', '.join(skipped['dangerous'])}")
    if skipped.get("unknown"):
        print(f"  - Unknown:   {', '.join(skipped['unknown'])}")

    print("\nServers configured:")
    for server_name, server_config in servers.items():
        safe_tools = server_config.get("safeTools", {})
        print(f"  {server_name}: {len(safe_tools)} safe tools")
        for tool_name in sorted(safe_tools.keys()):
            print(f"    - {tool_name}")

    print("\nNext steps:")
    print("  1. Review discovery_config.json")
    print("  2. Add or remove tools as needed")
    print("  3. Run: uv run mcp-discover")
    print("=" * 60 + "\n")


async def generate_discovery_config_file(
    mcp_config_path: str | None = None,
    output_path: str | None = None,
    skip_dangerous: bool = True,
) -> None:
    """
    Main entry point: generate discovery_config.json from mcp_config.json.

    Reads MCP server definitions, connects to discover tools, generates
    test parameters, and writes discovery_config.json.

    Args:
        mcp_config_path: Path to mcp_config.json (default: ./mcp_config.json)
        output_path: Path to write discovery_config.json (default: ./discovery_config.json)
        skip_dangerous: Skip dangerous tools by default (default: True)
    """
    import aiofiles

    from .config import McpConfig
    from .mcp_client import McpClientManager

    mcp_config_path_str = mcp_config_path or "./mcp_config.json"
    output_path_str = output_path or "./discovery_config.json"

    logger.info(f"Loading MCP config from: {mcp_config_path_str}")

    try:
        async with aiofiles.open(mcp_config_path_str) as f:
            content = await f.read()
        mcp_config_dict = json.loads(content)
        mcp_config = McpConfig.from_dict(mcp_config_dict)
    except FileNotFoundError:
        logger.error(f"mcp_config.json not found at {mcp_config_path_str}")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in mcp_config.json: {e}")
        return
    except Exception as e:
        logger.error(f"Failed to parse MCP config: {e}")
        return

    # Initialize MCP client manager
    manager = McpClientManager()
    try:
        await manager.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize MCP client: {e}")
        return

    # Discover tools from all servers using list_all_tools
    servers_tools: dict[str, list[dict[str, Any]]] = {}

    try:
        logger.debug("Discovering all tools from configured servers...")
        all_tools = await manager.list_all_tools()

        # Group tools by server name (extract from tool metadata)
        for tool in all_tools:
            # Tools don't inherently know their server, so we'll connect per server instead
            pass

        # Instead, iterate over enabled servers directly
        enabled_servers = mcp_config.get_enabled_servers()

        for server_name in enabled_servers.keys():
            try:
                logger.debug(f"Discovering tools from {server_name}...")

                # The manager caches tools, so we can get them from cache after list_all_tools
                # Using private method _get_server_tools since there's no public alternative
                tools = await manager._get_server_tools(server_name)

                tools_list: list[dict[str, Any]] = []
                for tool in tools:
                    tools_list.append(
                        {
                            "name": tool.name,
                            "description": tool.description or "",
                            "inputSchema": tool.inputSchema or {},
                        }
                    )

                servers_tools[server_name] = tools_list
                logger.info(f"Found {len(tools_list)} tools in {server_name}")

            except Exception as e:
                logger.warning(f"Failed to discover tools from {server_name}: {e}")
                continue

    except Exception as e:
        logger.error(f"Failed to list all tools: {e}")

    # Cleanup
    try:
        await manager.cleanup()
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

    # Build discovery config
    logger.info("Generating discovery config...")
    discovery_config = build_discovery_config(servers_tools, skip_dangerous=skip_dangerous)

    # Write config file
    try:
        async with aiofiles.open(output_path_str, "w") as f:
            config_content = json.dumps(discovery_config, indent=2)
            await f.write(config_content)
        logger.info(f"Wrote discovery config to: {output_path_str}")
    except Exception as e:
        logger.error(f"Failed to write discovery config: {e}")
        return

    # Print summary
    print_discovery_summary(discovery_config)


def main() -> None:
    """CLI entry point."""
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    asyncio.run(generate_discovery_config_file())


if __name__ == "__main__":
    main()
