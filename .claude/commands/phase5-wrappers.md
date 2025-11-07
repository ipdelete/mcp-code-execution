---
description: Phase 5 - Wrapper Generation
model: sonnet
---

# Phase 5: Wrapper Generation

**Goal**: Generate typed Python wrappers from MCP server tool definitions

**Tasks**: T076-T102 | **Validation**: CHK049-CHK062, CHK098, CHK100

## Prerequisites

- ✅ Phase 2 completed (MCP Client Manager)
- ✅ Phase 4 completed (Field Normalization)
- ✅ Test servers configured in `mcp_config.json`

## Context

This is the CORE of the progressive disclosure pattern. We generate:
1. **Pydantic models** from JSON Schema (params + results)
2. **Typed wrapper functions** for each tool
3. **Defensive unwrapping** in generated code
4. **Field normalization** integration

## Instructions

### 1. Create Schema Utilities Module (T076-T083)

Create `src/runtime/schema_utils.py`:

```python
"""
JSON Schema to Pydantic model conversion utilities.

Converts MCP tool schemas (JSON Schema format) to Pydantic model definitions.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Type


def json_schema_to_python_type(
    schema: Dict[str, Any], required: bool = True
) -> str:
    """
    Convert JSON Schema type to Python type hint string.

    Args:
        schema: JSON Schema definition
        required: Whether field is required

    Returns:
        Python type hint string (e.g., "str", "Optional[int]", "List[str]")

    Examples:
        >>> json_schema_to_python_type({"type": "string"}, True)
        'str'
        >>> json_schema_to_python_type({"type": "string"}, False)
        'Optional[str]'
        >>> json_schema_to_python_type({"type": "array", "items": {"type": "string"}})
        'List[str]'
    """
    # Handle union types: ["string", "null"]
    if isinstance(schema.get("type"), list):
        types = schema["type"]
        if "null" in types:
            required = False
            types = [t for t in types if t != "null"]
            if len(types) == 1:
                schema = {"type": types[0]}

    # Handle enum
    if "enum" in schema:
        enum_values = schema["enum"]
        # Use Literal type
        literal_values = ", ".join([f'"{v}"' for v in enum_values])
        base_type = f"Literal[{literal_values}]"
        return f"Optional[{base_type}]" if not required else base_type

    # Get base type
    schema_type = schema.get("type", "object")

    type_mapping = {
        "string": "str",
        "number": "float",
        "integer": "int",
        "boolean": "bool",
        "null": "None",
    }

    if schema_type in type_mapping:
        base_type = type_mapping[schema_type]
        return f"Optional[{base_type}]" if not required else base_type

    elif schema_type == "array":
        items_schema = schema.get("items", {"type": "object"})
        item_type = json_schema_to_python_type(items_schema, required=True)
        base_type = f"List[{item_type}]"
        return f"Optional[{base_type}]" if not required else base_type

    elif schema_type == "object":
        # Check for additionalProperties (Dict type)
        if "additionalProperties" in schema:
            value_schema = schema["additionalProperties"]
            if isinstance(value_schema, bool):
                value_type = "Any"
            else:
                value_type = json_schema_to_python_type(value_schema, required=True)
            base_type = f"Dict[str, {value_type}]"
            return f"Optional[{base_type}]" if not required else base_type

        # Otherwise, nested Pydantic model (will be generated separately)
        return "Dict[str, Any]" if required else "Optional[Dict[str, Any]]"

    # Fallback
    return "Any" if required else "Optional[Any]"


def generate_pydantic_model(
    model_name: str,
    schema: Dict[str, Any],
    description: Optional[str] = None,
) -> str:
    """
    Generate Pydantic model class from JSON Schema.

    Args:
        model_name: Name of the Pydantic model class
        schema: JSON Schema definition
        description: Optional model description

    Returns:
        Python code for Pydantic model

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "name": {"type": "string"},
        ...         "age": {"type": "integer"}
        ...     },
        ...     "required": ["name"]
        ... }
        >>> print(generate_pydantic_model("Person", schema))
        class Person(BaseModel):
            '''Generated model'''
            name: str
            age: Optional[int] = None
    """
    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))

    lines = [f"class {model_name}(BaseModel):"]

    # Add docstring
    if description:
        lines.append(f'    """{description}"""')
    else:
        lines.append('    """Generated Pydantic model."""')

    # Generate fields
    if not properties:
        lines.append("    pass")
    else:
        for field_name, field_schema in properties.items():
            is_required = field_name in required_fields
            field_type = json_schema_to_python_type(field_schema, is_required)
            field_desc = field_schema.get("description", "")

            if is_required:
                lines.append(f"    {field_name}: {field_type}")
            else:
                lines.append(f"    {field_name}: {field_type} = None")

            if field_desc:
                lines.append(f'    """{field_desc}"""')

    return "\n".join(lines)


def sanitize_name(name: str) -> str:
    """
    Sanitize name for Python identifier.

    Args:
        name: Original name

    Returns:
        Valid Python identifier

    Examples:
        >>> sanitize_name("my-tool")
        'my_tool'
        >>> sanitize_name("list")
        'list_'
    """
    # Replace hyphens with underscores
    name = name.replace("-", "_").replace(".", "_")

    # Handle Python keywords
    python_keywords = {"list", "dict", "set", "type", "class", "def", "import"}
    if name in python_keywords:
        name = name + "_"

    return name
```

### 2. Create Wrapper Generator Module (T084-T089)

Create `src/runtime/generate_wrappers.py`:

```python
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
from .mcp_client import McpClientManager
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
        async def git_status(params: GitStatusParams) -> GitStatusResult:
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
    result = await call_mcp_tool("{tool_identifier}", params.model_dump())

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
from runtime.servers.{server_name} import {tool_names[0] if tool_names else 'tool_name'}

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

    async with aiofiles.open(config_file, "r") as f:
        content = await f.read()
    config = McpConfig.model_validate_json(content)

    # Output directory
    output_dir = Path(__file__).parent.parent / "servers"
    output_dir.mkdir(exist_ok=True)

    # Generate for each server
    manager = McpClientManager()
    await manager.initialize(config_path)

    for server_name in config.mcpServers.keys():
        try:
            # Connect and list tools
            server_config = config.mcpServers[server_name]
            await manager._connect_to_server(server_name, server_config)
            client = manager._clients[server_name]
            tools_response = await client.list_tools()
            tools = tools_response.tools

            # Generate wrappers
            generate_server_module(server_name, tools, output_dir)

        except Exception as e:
            logger.error(f"Failed to generate wrappers for {server_name}: {e}")

    # Cleanup
    await manager.cleanup()

    logger.info("Wrapper generation complete!")


def main() -> None:
    """CLI entry point."""
    asyncio.run(generate_wrappers())


if __name__ == "__main__":
    main()
```

### 3. Create mcp_config.json (T117)

Create test configuration at project root:

```json
{
  "mcpServers": {
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"]
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    }
  }
}
```

### 4. Test Generation (T098-T099)

```bash
# Generate wrappers for test servers
uv run python -m runtime.generate_wrappers

# Check generated files
ls -R src/servers/

# Expected structure:
# src/servers/
#   git/
#     __init__.py
#     README.md
#     git_status.py
#     git_log.py
#     git_diff.py
#     ...
#   fetch/
#     __init__.py
#     README.md
#     fetch.py

# Verify generated code is valid Python
uv run python -c "from runtime.servers.git import git_status; print('✅ Import works')"

# Run mypy on generated code
uv run mypy src/servers/
```

### 5. Create Unit Tests (T100-T102)

Create `tests/unit/test_generate_wrappers.py`:

```python
"""Unit tests for wrapper generation."""

import pytest
from runtime.schema_utils import (
    json_schema_to_python_type,
    generate_pydantic_model,
    sanitize_name,
)


def test_json_schema_string_type():
    """Test string type conversion."""
    result = json_schema_to_python_type({"type": "string"}, required=True)
    assert result == "str"

    result = json_schema_to_python_type({"type": "string"}, required=False)
    assert result == "Optional[str]"


def test_json_schema_number_types():
    """Test number type conversions."""
    assert json_schema_to_python_type({"type": "number"}, True) == "float"
    assert json_schema_to_python_type({"type": "integer"}, True) == "int"


def test_json_schema_array_type():
    """Test array type conversion."""
    schema = {"type": "array", "items": {"type": "string"}}
    result = json_schema_to_python_type(schema, True)
    assert result == "List[str]"


def test_json_schema_enum_type():
    """Test enum (Literal) type conversion."""
    schema = {"enum": ["asc", "desc"]}
    result = json_schema_to_python_type(schema, True)
    assert 'Literal["asc", "desc"]' in result


def test_json_schema_union_type():
    """Test union type conversion."""
    schema = {"type": ["string", "null"]}
    result = json_schema_to_python_type(schema, True)
    assert result == "Optional[str]"


def test_json_schema_dict_type():
    """Test dict (additionalProperties) type conversion."""
    schema = {"type": "object", "additionalProperties": {"type": "string"}}
    result = json_schema_to_python_type(schema, True)
    assert result == "Dict[str, str]"


def test_generate_pydantic_model_simple():
    """Test simple Pydantic model generation."""
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name"],
    }

    result = generate_pydantic_model("Person", schema)

    assert "class Person(BaseModel):" in result
    assert "name: str" in result
    assert "age: Optional[int] = None" in result


def test_sanitize_name():
    """Test name sanitization."""
    assert sanitize_name("my-tool") == "my_tool"
    assert sanitize_name("my.tool") == "my_tool"
    assert sanitize_name("list") == "list_"
```

```bash
# Run tests
uv run pytest tests/unit/test_generate_wrappers.py -v
```

## Validation Checklist

- [ ] CHK049-CHK053 - JSON Schema types handled (string, number, boolean, null, array, object)?
- [ ] CHK054 - Required vs optional fields distinguished?
- [ ] CHK055 - Wrapper includes docstrings from tool descriptions?
- [ ] CHK056 - Defensive unwrapping in generated wrappers?
- [ ] CHK057 - Field normalization integrated?
- [ ] CHK058 - Custom utils.py preserved?
- [ ] CHK059 - Barrel exports (__init__.py) created?
- [ ] CHK060 - Per-server README.md generated?
- [ ] CHK061 - CLI command (mcp-generate) works?
- [ ] CHK062 - Generated wrappers tested with git and fetch?
- [ ] CHK098 - Unit tests for schema conversion?
- [ ] CHK100 - Unit tests for wrapper generation?

## Deliverables

- ✅ `src/runtime/schema_utils.py` with JSON Schema conversion
- ✅ `src/runtime/generate_wrappers.py` with wrapper generation
- ✅ Generated wrappers in `src/servers/`
- ✅ `tests/unit/test_generate_wrappers.py` with unit tests
- ✅ CLI command `uv run mcp-generate` works

## Troubleshooting

**Issue**: Generated code has syntax errors
```bash
# Check generated files with Python parser
python -m py_compile src/servers/git/git_status.py
```

**Issue**: Type hints invalid
```bash
# Run mypy on generated code
uv run mypy src/servers/
```

**Issue**: Import errors
```python
# Ensure __init__.py exports are correct
# Check that all imports use absolute imports from runtime
```

---

**Next Phase**: Proceed to `/phase7-integration` (Phase 6 is optional)
