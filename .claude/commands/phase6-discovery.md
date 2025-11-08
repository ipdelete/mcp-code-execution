---
description: Phase 6 - Schema Discovery
model: sonnet
---

# Phase 6: Schema Discovery

**Goal**: Generate Pydantic models from actual API responses (for servers without output schemas)

**Tasks**: T103-T116 | **Validation**: CHK063-CHK071

## Context: Read plan.md First

Review `plan.md` section: **Phase 6: Schema Discovery (lines 707-792)** for comprehensive type inference patterns, safe tool execution strategy, and defensive coding philosophy.

## Prerequisites

- ✅ Phase 2 completed (MCP Client Manager)
- ✅ Phase 5 completed (Wrapper Generation)
- ✅ Test servers configured in `mcp_config.json`
- ✅ `discovery_config.json` ready (defines safe tools)

## Context

This phase **infers Pydantic models from actual responses** when servers lack output schemas. Key patterns:

1. **Safe execution** - Only read-only tools (no side effects)
2. **Type inference** - Deduce Python types from response data
3. **Defensive coding** - All fields Optional (handle missing data)
4. **Metadata preservation** - Document tool description and sample params

## Instructions

### 1. Create discovery_config.example.json (T103)

Create `discovery_config.example.json` at root:

```json
{
  "servers": {
    "git": {
      "safeTools": {
        "git_status": {
          "repo_path": "."
        },
        "git_log": {
          "repo_path": ".",
          "max_count": 1
        }
      }
    },
    "fetch": {
      "safeTools": {
        "fetch": {
          "url": "https://example.com",
          "timeout": 5
        }
      }
    },
    "github": {
      "safeTools": {
        "search_code": {
          "q": "language:python hello",
          "per_page": 1
        },
        "search_repositories": {
          "q": "stars:>1000",
          "per_page": 1
        }
      }
    }
  }
}
```

### 2. Create Schema Inference Utilities

Create `src/runtime/schema_inference.py`:

```python
"""
Type inference utilities for discovering Pydantic models from API responses.

This module infers Pydantic models from actual response data when output
schemas are not available or incomplete.
"""

from typing import Any, Dict, List, Optional, Set
from collections import defaultdict


def infer_python_type(value: Any) -> str:
    """
    Infer Python type from a value.

    Args:
        value: The value to infer type from

    Returns:
        Python type hint string (e.g., "str", "int", "List[str]")

    Examples:
        >>> infer_python_type("hello")
        'str'
        >>> infer_python_type(42)
        'int'
        >>> infer_python_type([1, 2, 3])
        'List[int]'
    """
    if value is None:
        return "Optional[Any]"
    elif isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "str"
    elif isinstance(value, list):
        if not value:
            return "List[Any]"
        # Infer from first element
        item_type = infer_python_type(value[0])
        return f"List[{item_type}]"
    elif isinstance(value, dict):
        if not value:
            return "Dict[str, Any]"
        # Check if all values have same type
        value_types = set(infer_python_type(v) for v in value.values())
        if len(value_types) == 1:
            value_type = value_types.pop()
            return f"Dict[str, {value_type}]"
        else:
            return "Dict[str, Any]"
    else:
        return "Any"


def infer_pydantic_model_from_response(
    tool_name: str,
    response_data: Any,
    description: Optional[str] = None,
) -> str:
    """
    Infer Pydantic model from actual response data.

    All fields are marked Optional for defensive coding (handle missing data).

    Args:
        tool_name: Name of the tool that produced response
        response_data: Actual response data from tool execution
        description: Optional tool description

    Returns:
        Python code for Pydantic model

    Example:
        >>> response = {"name": "John", "age": 30, "tags": ["python", "mcp"]}
        >>> code = infer_pydantic_model_from_response("get_user", response)
        >>> print(code)
        class GetUserResult(BaseModel):
            '''Result from get_user tool.'''
            name: Optional[str] = None
            age: Optional[int] = None
            tags: Optional[List[str]] = None
    """
    # Normalize tool name for model name
    model_name = "".join(word.capitalize() for word in tool_name.split("_")) + "Result"

    if not isinstance(response_data, dict):
        # Non-dict responses become wrapped
        inferred_type = infer_python_type(response_data)
        return f"""
class {model_name}(BaseModel):
    '''Result from {tool_name} tool.'''
    value: {inferred_type} = None
"""

    # Build model fields from dict
    lines = [f"class {model_name}(BaseModel):"]

    # Add docstring
    if description:
        lines.append(f'    """{description}"""')
    else:
        lines.append(f'    """Result from {tool_name} tool."""')

    # Generate fields (all Optional for defensive coding)
    if not response_data:
        lines.append("    pass")
    else:
        for key, value in response_data.items():
            # Sanitize field name
            field_name = key.replace("-", "_").replace(".", "_")
            if field_name.startswith("_"):
                field_name = field_name[1:]

            inferred_type = infer_python_type(value)
            # All fields Optional (defensive)
            if inferred_type.startswith("Optional"):
                lines.append(f"    {field_name}: {inferred_type} = None")
            else:
                lines.append(f"    {field_name}: Optional[{inferred_type}] = None")

    return "\n".join(lines)


def merge_response_schemas(
    schemas: List[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Merge multiple response schemas into unified field types.

    When executing the same tool with different parameters, we may get
    slightly different response structures. This merges them conservatively.

    Args:
        schemas: List of response schemas to merge

    Returns:
        Dict mapping field name to merged type hint
    """
    if not schemas:
        return {}

    if len(schemas) == 1:
        return {
            key: infer_python_type(value)
            for key, value in schemas[0].items()
        }

    # Find all field names across all schemas
    all_fields = set()
    for schema in schemas:
        if isinstance(schema, dict):
            all_fields.update(schema.keys())

    # Merge types conservatively (use Any if types differ)
    merged = {}
    for field in all_fields:
        field_types = set()
        for schema in schemas:
            if isinstance(schema, dict) and field in schema:
                field_types.add(infer_python_type(schema[field]))

        if len(field_types) == 1:
            # Consistent type
            merged[field] = field_types.pop()
        else:
            # Mixed types - use Any
            merged[field] = "Any"

    return merged
```

### 3. Create Schema Discovery Module (T104-T113)

Create `src/runtime/discover_schemas.py`:

```python
"""
Generate Pydantic models from actual API responses.

This module discovers Pydantic models by executing safe tools and inferring
types from their responses. Useful for servers that don't provide output schemas.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

from .config import McpConfig
from .exceptions import ConfigurationError, ToolExecutionError
from .mcp_client import McpClientManager
from .schema_inference import (
    infer_pydantic_model_from_response,
    merge_response_schemas,
)

logger = logging.getLogger("mcp_execution.discover_schemas")


async def execute_safe_tool(
    manager: McpClientManager,
    server_name: str,
    tool_name: str,
    params: Dict[str, Any],
) -> Any:
    """
    Execute a tool safely (read-only operations only).

    Args:
        manager: MCP client manager
        server_name: Name of server
        tool_name: Name of tool
        params: Tool parameters

    Returns:
        Response from tool

    Raises:
        ToolExecutionError: If tool fails or has side effects
    """
    tool_id = f"{server_name}__{tool_name}"

    logger.debug(f"Executing safe tool: {tool_id} with params: {params}")

    try:
        result = await manager.call_tool(tool_id, params)

        # Defensive unwrapping
        unwrapped = getattr(result, "value", result)

        return unwrapped
    except Exception as e:
        raise ToolExecutionError(
            f"Failed to execute safe tool {tool_id}: {e}"
        ) from e


async def discover_server_schemas(
    manager: McpClientManager,
    server_name: str,
    safe_tools_config: Dict[str, Dict[str, Any]],
) -> Dict[str, str]:
    """
    Discover Pydantic models for a single server's tools.

    Args:
        manager: MCP client manager
        server_name: Name of server
        safe_tools_config: Dict mapping tool name to sample params

    Returns:
        Dict mapping tool name to Pydantic model code
    """
    logger.info(f"Discovering schemas for server: {server_name}")

    discovered_models = {}

    for tool_name, sample_params in safe_tools_config.items():
        try:
            logger.debug(f"Discovering schema for {server_name}.{tool_name}")

            # Execute with sample parameters
            response = await execute_safe_tool(
                manager, server_name, tool_name, sample_params
            )

            # Generate Pydantic model from response
            model_code = infer_pydantic_model_from_response(
                tool_name, response
            )

            discovered_models[tool_name] = model_code

            logger.debug(f"✓ Discovered schema for {tool_name}")

        except Exception as e:
            logger.warning(
                f"Failed to discover schema for {tool_name}: {e}"
            )
            # Continue with other tools
            continue

    return discovered_models


async def write_discovered_types(
    server_name: str,
    discovered_models: Dict[str, str],
    output_dir: Path,
) -> None:
    """
    Write discovered Pydantic models to file.

    Creates: src/servers/{server}/discovered_types.py

    Args:
        server_name: Name of server
        discovered_models: Dict mapping tool name to model code
        output_dir: Output directory (src/servers/)
    """
    server_dir = output_dir / server_name
    server_dir.mkdir(parents=True, exist_ok=True)

    discovered_file = server_dir / "discovered_types.py"

    # Build file content
    lines = [
        '"""',
        f"Discovered Pydantic models for {server_name} server.",
        "",
        "WARNING: These models are inferred from actual API responses.",
        "They may be incomplete or incorrect. Use with caution.",
        "All fields are Optional for defensive coding.",
        '"""',
        "",
        "from pydantic import BaseModel",
        "from typing import Any, Dict, List, Optional",
        "",
    ]

    # Add all discovered models
    for tool_name, model_code in discovered_models.items():
        lines.append(model_code)
        lines.append("")

    content = "\n".join(lines)

    async with aiofiles.open(discovered_file, "w") as f:
        await f.write(content)

    logger.info(f"Wrote discovered types to: {discovered_file}")


async def discover_schemas(config_path: Path | None = None) -> None:
    """
    Main schema discovery orchestrator.

    1. Load discovery_config.json
    2. For each configured server:
       a. Connect to server
       b. Execute safe tools with sample params
       c. Infer Pydantic models from responses
       d. Write to src/servers/{server}/discovered_types.py
    3. Log results

    Args:
        config_path: Path to discovery_config.json
    """
    logger.info("Starting schema discovery...")

    # Load discovery config
    config_file = config_path or Path.cwd() / "discovery_config.json"

    if not config_file.exists():
        logger.warning(
            f"Discovery config not found: {config_file}. "
            "Skipping schema discovery."
        )
        return

    try:
        async with aiofiles.open(config_file, "r") as f:
            content = await f.read()
        discovery_config = json.loads(content)
    except Exception as e:
        logger.error(f"Failed to load discovery config: {e}")
        return

    # Initialize MCP client manager
    manager = McpClientManager()
    try:
        await manager.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize MCP client: {e}")
        return

    # Output directory
    output_dir = Path(__file__).parent.parent / "servers"
    output_dir.mkdir(exist_ok=True)

    # Discover schemas for each server
    servers_config = discovery_config.get("servers", {})
    for server_name, server_config in servers_config.items():
        try:
            safe_tools_config = server_config.get("safeTools", {})

            if not safe_tools_config:
                logger.debug(
                    f"No safe tools configured for {server_name}, skipping"
                )
                continue

            # Discover schemas
            discovered_models = await discover_server_schemas(
                manager, server_name, safe_tools_config
            )

            if discovered_models:
                # Write discovered types
                await write_discovered_types(
                    server_name, discovered_models, output_dir
                )
                logger.info(
                    f"✓ Discovered {len(discovered_models)} "
                    f"schemas for {server_name}"
                )
            else:
                logger.warning(f"No schemas discovered for {server_name}")

        except Exception as e:
            logger.error(
                f"Failed to discover schemas for {server_name}: {e}"
            )
            continue

    # Cleanup
    try:
        await manager.cleanup()
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

    logger.info("Schema discovery complete!")


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
    )
    asyncio.run(discover_schemas())


if __name__ == "__main__":
    main()
```

### 4. Add Script Alias to pyproject.toml (T115)

Update `pyproject.toml` `[project.scripts]` section:

```toml
[project.scripts]
mcp-exec = "runtime.harness:main"
mcp-generate = "runtime.generate_wrappers:main"
mcp-discover = "runtime.discover_schemas:main"
```

### 5. Update package.json for Compatibility (T139)

If using npm scripts for compatibility:

```json
{
  "scripts": {
    "generate": "uv run python -m runtime.generate_wrappers",
    "discover-schemas": "uv run python -m runtime.discover_schemas",
    "exec": "uv run python -m runtime.harness"
  }
}
```

### 6. Create Unit Tests (Optional)

Create `tests/unit/test_schema_inference.py`:

```python
"""Unit tests for schema inference."""

import pytest
from runtime.schema_inference import (
    infer_python_type,
    infer_pydantic_model_from_response,
    merge_response_schemas,
)


def test_infer_python_type_primitives():
    """Test primitive type inference."""
    assert infer_python_type("hello") == "str"
    assert infer_python_type(42) == "int"
    assert infer_python_type(3.14) == "float"
    assert infer_python_type(True) == "bool"
    assert infer_python_type(None) == "Optional[Any]"


def test_infer_python_type_list():
    """Test list type inference."""
    assert infer_python_type([1, 2, 3]) == "List[int]"
    assert infer_python_type(["a", "b"]) == "List[str]"
    assert infer_python_type([]) == "List[Any]"


def test_infer_python_type_dict():
    """Test dict type inference."""
    assert infer_python_type({"name": "John"}) == "Dict[str, str]"
    assert infer_python_type({"count": 42}) == "Dict[str, int]"
    assert infer_python_type({}) == "Dict[str, Any]"


def test_infer_pydantic_model_simple():
    """Test simple model inference."""
    response = {"name": "John", "age": 30}
    code = infer_pydantic_model_from_response("get_user", response)

    assert "class GetUserResult(BaseModel):" in code
    assert "name: Optional[str] = None" in code
    assert "age: Optional[int] = None" in code


def test_infer_pydantic_model_nested():
    """Test nested structure inference."""
    response = {
        "user": {"name": "John", "age": 30},
        "tags": ["python", "mcp"],
    }
    code = infer_pydantic_model_from_response("get_user", response)

    assert "class GetUserResult(BaseModel):" in code
    assert "user: Optional[Dict[str, Any]] = None" in code
    assert "tags: Optional[List[str]] = None" in code


def test_merge_response_schemas():
    """Test schema merging."""
    schemas = [
        {"name": "John", "age": 30},
        {"name": "Jane", "age": 25},
    ]

    merged = merge_response_schemas(schemas)

    assert merged["name"] == "str"
    assert merged["age"] == "int"


def test_merge_response_schemas_mixed_types():
    """Test merging with mixed types."""
    schemas = [
        {"id": 1},  # int
        {"id": "abc"},  # str
    ]

    merged = merge_response_schemas(schemas)

    # Mixed types default to Any
    assert merged["id"] == "Any"
```

### 7. Test Discovery (T116)

```bash
# Copy discovery config for testing
cp discovery_config.example.json discovery_config.json

# Run schema discovery with safe tools
uv run python -m runtime.discover_schemas

# Check discovered types
ls -la src/servers/*/discovered_types.py

# Expected output:
# src/servers/git/discovered_types.py
# src/servers/fetch/discovered_types.py
# etc.

# Validate syntax
uv run python -m py_compile src/servers/git/discovered_types.py

# Check with mypy
uv run mypy src/servers/*/discovered_types.py
```

## Key Patterns

### Defensive Coding
All fields are `Optional[T] = None` to handle:
- Missing fields in responses
- Incomplete responses
- API changes

```python
class GetUserResult(BaseModel):
    name: Optional[str] = None  # Safe even if missing
    age: Optional[int] = None
```

### Safe Tool Execution
Only execute read-only tools:
- ❌ Never execute tools that modify state
- ❌ No file writes, deletes, or updates
- ✅ Only queries and reads

```python
# ✅ Safe: read operations
"git_status": {"repo_path": "."}
"fetch": {"url": "https://example.com"}

# ❌ Dangerous: write operations
"write_file": {"path": "...", "content": "..."}
"delete_file": {"path": "..."}
```

### Type Inference
Infers from actual response data:

```
str → str
42 → int
[1,2] → List[int]
{"a": "b"} → Dict[str, str]
None → Optional[Any]
```

## Validation Checklist

- [ ] CHK063 - discovery_config.json loads successfully?
- [ ] CHK064 - Only safe (read-only) tools execute?
- [ ] CHK065 - Responses properly unwrapped (.value)?
- [ ] CHK066 - Type inference handles all Python types?
- [ ] CHK067 - Arrays handled with first element template?
- [ ] CHK068 - All fields Optional (defensive)?
- [ ] CHK069 - Types written to discovered_types.py?
- [ ] CHK070 - Warning comments included?
- [ ] CHK071 - discovery_config.example.json provided?

## Deliverables

- ✅ `discovery_config.example.json` with safe tool examples
- ✅ `src/runtime/schema_inference.py` with type inference
- ✅ `src/runtime/discover_schemas.py` with discovery orchestrator
- ✅ Generated `src/servers/{server}/discovered_types.py` files
- ✅ CLI command `uv run mcp-discover` works

## Troubleshooting

**Issue**: Tool execution fails
```bash
# Check safe tools config
cat discovery_config.json

# Verify tool params are valid for sample data
# Adjust sample params in discovery_config.json
```

**Issue**: Type inference seems wrong
```python
# Check inferred type for specific value
from runtime.schema_inference import infer_python_type
infer_python_type({"complex": "data"})
```

**Issue**: Generated models have syntax errors
```bash
# Validate Python syntax
python -m py_compile src/servers/git/discovered_types.py

# Check generated file directly
cat src/servers/git/discovered_types.py
```

## Mark Items Complete

After successfully completing this phase, mark the following as complete:

### Update CHECKLIST.md (CHK063-CHK071)
```bash
# Mark Phase 6 checklist items complete
for i in {063..071}; do
  sed -i '' "s/^- \\[ \\] CHK$i/- [x] CHK$i/" CHECKLIST.md
done

echo "✅ Phase 6 checklist items marked complete"
```

### Update TASKS.md (T103-T116)
```bash
# Mark Phase 6 task items complete
for i in {103..116}; do
  sed -i '' "s/^- \\[ \\] T$i/- [x] T$i/" TASKS.md
done

echo "✅ Phase 6 task items marked complete"
```

### Verify Completion
```bash
echo "✅ Phase 6 complete and documented"
```

---

**Next Phase**: Proceed to `/phase7-integration` (Phase 7: Integration Testing & Example Script)

**Notes**:
- Phase 6 is **OPTIONAL (P1)** - Not required for MVP
- Can be skipped if all servers provide output schemas
- Useful for APIs that lack documentation
- Always prefer explicit schemas over inference when available
