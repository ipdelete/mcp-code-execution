# Type Safety with mypy

The Python port uses strict type hints validated by mypy.

## Configuration

See `pyproject.toml`:

```toml
[tool.mypy]
strict = true
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## Running mypy

```bash
# Check all source code
uv run mypy src/

# Check specific file
uv run mypy src/runtime/mcp_client.py

# Check tests
uv run mypy tests/
```

## Type Hints Best Practices

### Function Signatures

```python
# ✅ Good: Full type hints
async def call_tool(
    tool_identifier: str,
    params: Dict[str, Any]
) -> Any:
    ...

# ❌ Bad: Missing type hints
async def call_tool(tool_identifier, params):
    ...
```

### Optional vs None

```python
from typing import Optional

# ✅ Use Optional for nullable values
def get_config(path: Optional[Path] = None) -> McpConfig:
    ...

# ❌ Don't use None without Optional
def get_config(path: Path = None) -> McpConfig:  # mypy error
    ...
```

### Generic Collections

```python
from typing import Dict, List, Any

# ✅ Specify element types
tools: List[str] = ["tool1", "tool2"]
config: Dict[str, Any] = {"key": "value"}

# ❌ Avoid bare list/dict
tools: list = ["tool1", "tool2"]  # mypy warning
```

### Type Aliases

```python
from typing import Dict, Any

# Create reusable type aliases
JsonDict = Dict[str, Any]
ToolParams = Dict[str, Any]

def process(data: JsonDict) -> ToolParams:
    ...
```

## Handling Any Types

Sometimes `Any` is necessary for dynamic MCP responses:

```python
from typing import Any, cast

# Accept Any, but validate before use
def process_result(result: Any) -> Dict[str, str]:
    # Runtime validation
    if isinstance(result, dict):
        return cast(Dict[str, str], result)
    raise TypeError(f"Expected dict, got {type(result)}")
```

## Generated Code Type Safety

Generated wrappers are fully typed:

```python
# Generated wrapper (type-safe)
async def git_status(params: GitStatusParams) -> GitStatusResult:
    """Get git repository status."""
    result = await call_mcp_tool("git__git_status", params.model_dump())
    return GitStatusResult.model_validate(result)
```

## IDE Support

Type hints enable:
- ✅ Autocomplete
- ✅ Inline documentation
- ✅ Error detection
- ✅ Refactoring support

### VS Code Setup

Install Pylance extension:
```json
{
  "python.analysis.typeCheckingMode": "strict"
}
```

### PyCharm Setup

Enable type checking in Settings → Editor → Inspections → Python → Type Checker.
