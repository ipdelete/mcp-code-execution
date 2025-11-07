---
description: Phase 4 - Field Normalization
model: sonnet
---

# Phase 4: Field Normalization

**Goal**: Normalize inconsistent field casing from different APIs

**Tasks**: T065-T075 | **Validation**: CHK042-CHK048, CHK099

## Context: Read plan.md First

Review `plan.md` section: **Phase 4 (Detailed): Field Normalization Implementation (lines 794-898)** for normalization strategy patterns and ADO field rules.

## Prerequisites

- ✅ Phase 1 completed (project setup)
- ✅ Understanding of normalization requirements from plan.md

## Context

Different MCP servers return fields with inconsistent casing:
- **Azure DevOps (ADO)**: Returns `system.*` but expects `System.*`
- **GitHub, Filesystem**: No normalization needed

This phase implements a pluggable normalization strategy to handle these cases.

## Instructions

### 1. Create Normalization Module (T065-T067)

Create `src/runtime/normalize_fields.py`:

```python
"""
Field normalization utilities for handling inconsistent API casing.

Some MCP servers (e.g., Azure DevOps) return fields with lowercase prefixes
but expect PascalCase prefixes in certain contexts. This module provides
configurable normalization strategies.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel

# Type alias for normalization strategies
NormalizationStrategy = Literal["none", "ado-pascal-case"]


class NormalizationConfig(BaseModel):
    """Configuration for field normalization per server."""

    servers: Dict[str, NormalizationStrategy]

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


# Default configuration
NORMALIZATION_CONFIG = NormalizationConfig(
    servers={
        "ado": "ado-pascal-case",
        "filesystem": "none",
        "github": "none",
    }
)
```

### 2. Implement Strategy Dispatcher (T068)

Add to `normalize_fields.py`:

```python
def normalize_field_names(obj: Any, server_name: str) -> Any:
    """
    Normalize field names based on server strategy.

    Recursively traverses dicts and lists.
    Returns new object (immutable).

    Args:
        obj: Object to normalize (dict, list, or primitive)
        server_name: Name of the server (determines strategy)

    Returns:
        Normalized object (new instance, original unchanged)

    Examples:
        >>> normalize_field_names({"system.title": "foo"}, "ado")
        {'System.Title': 'foo'}

        >>> normalize_field_names({"title": "foo"}, "github")
        {'title': 'foo'}
    """
    strategy = NORMALIZATION_CONFIG.servers.get(server_name, "none")

    if strategy == "none":
        return obj
    elif strategy == "ado-pascal-case":
        return normalize_ado_fields(obj)
    else:
        # Unknown strategy, return unchanged
        return obj
```

### 3. Implement ADO Normalization (T069-T071)

Add ADO-specific normalization:

```python
def normalize_ado_fields(obj: Any) -> Any:
    """
    ADO-specific field normalization.

    Rules:
    - system.* → System.*
    - microsoft.* → Microsoft.*
    - custom.* → Custom.*
    - wef_* → WEF_*

    Recursively processes nested structures.
    Returns new object (immutable).

    Args:
        obj: Object to normalize

    Returns:
        Normalized object (new instance)

    Examples:
        >>> normalize_ado_fields({"system.title": "foo"})
        {'System.title': 'foo'}

        >>> normalize_ado_fields({"fields": {"system.id": 123}})
        {'fields': {'System.id': 123}}
    """
    # Handle primitives
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    # Handle lists
    if isinstance(obj, list):
        return [normalize_ado_fields(item) for item in obj]

    # Handle dicts
    if isinstance(obj, dict):
        normalized = {}
        for key, value in obj.items():
            new_key = key

            # Apply normalization rules
            if key.startswith("system."):
                new_key = "System." + key[7:]
            elif key.startswith("microsoft."):
                new_key = "Microsoft." + key[10:]
            elif key.startswith("custom."):
                new_key = "Custom." + key[7:]
            elif key.startswith("wef_"):
                new_key = "WEF_" + key[4:]

            # Recursively normalize value
            normalized[new_key] = normalize_ado_fields(value)

        return normalized

    # Unknown type, return as-is
    return obj
```

### 4. Add Configuration Override (T066)

Add configuration management:

```python
def update_normalization_config(
    server_name: str, strategy: NormalizationStrategy
) -> None:
    """
    Update normalization strategy for a server.

    Args:
        server_name: Name of the server
        strategy: Normalization strategy to use

    Examples:
        >>> update_normalization_config("myserver", "ado-pascal-case")
        >>> update_normalization_config("myserver", "none")
    """
    NORMALIZATION_CONFIG.servers[server_name] = strategy


def get_normalization_strategy(server_name: str) -> NormalizationStrategy:
    """
    Get normalization strategy for a server.

    Args:
        server_name: Name of the server

    Returns:
        Normalization strategy (defaults to "none")
    """
    return NORMALIZATION_CONFIG.servers.get(server_name, "none")
```

### 5. Create Unit Tests (T072-T074)

Create `tests/unit/test_normalize_fields.py`:

```python
"""Unit tests for field normalization."""

import pytest

from runtime.normalize_fields import (
    normalize_ado_fields,
    normalize_field_names,
    update_normalization_config,
)


def test_ado_normalization_system_fields():
    """Test ADO normalization for system.* fields."""
    input_obj = {"system.title": "Task Title", "system.id": 123}

    result = normalize_ado_fields(input_obj)

    assert result == {"System.title": "Task Title", "System.id": 123}


def test_ado_normalization_microsoft_fields():
    """Test ADO normalization for microsoft.* fields."""
    input_obj = {"microsoft.vsts.common.priority": 1}

    result = normalize_ado_fields(input_obj)

    assert result == {"Microsoft.vsts.common.priority": 1}


def test_ado_normalization_custom_fields():
    """Test ADO normalization for custom.* fields."""
    input_obj = {"custom.myfield": "value"}

    result = normalize_ado_fields(input_obj)

    assert result == {"Custom.myfield": "value"}


def test_ado_normalization_wef_fields():
    """Test ADO normalization for wef_* fields."""
    input_obj = {"wef_123": "value"}

    result = normalize_ado_fields(input_obj)

    assert result == {"WEF_123": "value"}


def test_ado_normalization_nested_structures():
    """Test ADO normalization with nested dicts and lists."""
    input_obj = {
        "fields": {"system.title": "Title", "custom.status": "Active"},
        "tags": ["system.tag1", "system.tag2"],
    }

    result = normalize_ado_fields(input_obj)

    assert result == {
        "fields": {"System.title": "Title", "Custom.status": "Active"},
        "tags": ["system.tag1", "system.tag2"],  # Strings unchanged
    }


def test_ado_normalization_immutability():
    """Test that normalization returns new object (immutable)."""
    original = {"system.title": "Original"}

    result = normalize_ado_fields(original)

    # Modify result
    result["system.title"] = "Modified"

    # Original unchanged
    assert original == {"system.title": "Original"}


def test_ado_normalization_primitives():
    """Test that primitives are returned unchanged."""
    assert normalize_ado_fields(None) is None
    assert normalize_ado_fields("string") == "string"
    assert normalize_ado_fields(123) == 123
    assert normalize_ado_fields(True) is True


def test_ado_normalization_recursion():
    """Test deep recursion with nested structures."""
    input_obj = {
        "level1": {
            "level2": {"level3": {"system.field": "deep"}},
            "list": [{"system.item": 1}, {"system.item": 2}],
        }
    }

    result = normalize_ado_fields(input_obj)

    assert result == {
        "level1": {
            "level2": {"level3": {"System.field": "deep"}},
            "list": [{"System.item": 1}, {"System.item": 2}],
        }
    }


def test_normalize_field_names_strategy_dispatch():
    """Test that normalize_field_names dispatches to correct strategy."""
    input_obj = {"system.title": "Title"}

    # Test ADO strategy
    result_ado = normalize_field_names(input_obj, "ado")
    assert result_ado == {"System.title": "Title"}

    # Test none strategy
    result_none = normalize_field_names(input_obj, "github")
    assert result_none == {"system.title": "Title"}


def test_update_normalization_config():
    """Test updating normalization configuration."""
    update_normalization_config("myserver", "ado-pascal-case")

    input_obj = {"system.title": "Title"}
    result = normalize_field_names(input_obj, "myserver")

    assert result == {"System.title": "Title"}
```

### 6. Run Tests (T075)

```bash
# Run unit tests
uv run pytest tests/unit/test_normalize_fields.py -v

# Run with coverage
uv run pytest tests/unit/test_normalize_fields.py --cov=src/runtime/normalize_fields

# Expected: All tests passing
```

## Validation Checklist

- [ ] CHK042 - Pluggable normalization strategies implemented?
- [ ] CHK043 - "ado-pascal-case" strategy fully specified?
- [ ] CHK044 - Recursive traversal on nested dicts and lists?
- [ ] CHK045 - Normalization is immutable (returns new objects)?
- [ ] CHK046 - NormalizationConfig typed with Pydantic?
- [ ] CHK047 - Users can configure normalization per server?
- [ ] CHK048 - Default configuration documented?
- [ ] CHK099 - Unit tests exist for normalization?

## Deliverables

- ✅ `src/runtime/normalize_fields.py` with complete implementation
- ✅ `tests/unit/test_normalize_fields.py` with comprehensive tests
- ✅ All tests passing

## Usage Examples

### Example 1: Normalize ADO Response

```python
from runtime.normalize_fields import normalize_field_names

# ADO returns lowercase prefixes
ado_response = {
    "fields": {
        "system.title": "Task",
        "system.assignedTo": "user@example.com",
        "custom.priority": "High"
    }
}

# Normalize for ADO
normalized = normalize_field_names(ado_response, "ado")

# Result:
# {
#     "fields": {
#         "System.title": "Task",
#         "System.assignedTo": "user@example.com",
#         "Custom.priority": "High"
#     }
# }
```

### Example 2: No Normalization for GitHub

```python
github_response = {
    "title": "Issue Title",
    "labels": ["bug", "enhancement"]
}

normalized = normalize_field_names(github_response, "github")

# Result: unchanged (strategy is "none")
# {
#     "title": "Issue Title",
#     "labels": ["bug", "enhancement"]
# }
```

### Example 3: Custom Configuration

```python
from runtime.normalize_fields import update_normalization_config

# Add custom server with ADO normalization
update_normalization_config("myado", "ado-pascal-case")

# Now normalization works for "myado" server
response = {"system.field": "value"}
normalized = normalize_field_names(response, "myado")
# Result: {"System.field": "value"}
```

## Integration Points

This module will be used in Phase 5 (Wrapper Generation):

```python
# In generate_wrappers.py
from runtime.normalize_fields import normalize_field_names

async def generate_tool_wrapper(server_name: str, tool: Tool) -> str:
    # ... wrapper generation code ...

    # Add normalization in generated wrapper
    wrapper_code = f'''
async def {tool_name}(params: {params_model}) -> {result_model}:
    result = await call_mcp_tool("{server_name}__{tool_name}", params.model_dump())

    # Apply field normalization
    from runtime.normalize_fields import normalize_field_names
    normalized = normalize_field_names(result, "{server_name}")

    return {result_model}.model_validate(normalized)
'''
```

## Troubleshooting

**Issue**: Tests failing with import errors
```bash
# Ensure editable install
uv pip install -e .
```

**Issue**: Recursion depth errors
```python
# Check for circular references in input data
# normalize_ado_fields handles standard nested structures
```

## Mark Items Complete

After successfully completing this phase, mark the following as complete:

### Update CHECKLIST.md (CHK042-CHK048, CHK099)
```bash
# Mark Phase 4 checklist items complete
for i in {042..048}; do
  sed -i '' "s/^- \[ \] CHK$i/- [x] CHK$i/" CHECKLIST.md
done

sed -i '' 's/^- \[ \] CHK099/- [x] CHK099/' CHECKLIST.md

echo "✅ Phase 4 checklist items marked complete"
```

### Update TASKS.md (T065-T075)
```bash
# Mark Phase 4 task items complete
for i in {065..075}; do
  sed -i '' "s/^- \[ \] T$i/- [x] T$i/" TASKS.md
done

echo "✅ Phase 4 task items marked complete"
```

### Verify Completion
```bash
echo "✅ Phase 4 complete and documented"
```

---

**Next Phase**: Proceed to `/phase5-wrappers` to implement wrapper generation
