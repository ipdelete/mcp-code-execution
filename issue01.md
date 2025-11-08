# MCP Protocol: Tool Capabilities and Output Schema Documentation

## Problem Statement

**The Missing Output Schema Problem**: The MCP specification makes `outputSchema` optional rather than required for tool definitions. While this pragmatic design choice enables broader real-world adoption, it creates a significant challenge for client implementations trying to provide type-safe tool wrappers and scripts.

### The Core Issue

When generating typed Python wrappers and scripts for MCP tools:
- If `outputSchema` is provided → Can generate precise Pydantic models and type hints
- If `outputSchema` is missing (common case) → Must fall back to generic `Dict[str, Any]` types

This lack of structure creates several downstream problems:

1. **Type Safety Lost**: Without output schemas, IDEs cannot provide autocomplete or type checking
2. **Runtime Unpredictability**: Tools can return strings, lists, dicts, or objects - no consistency
3. **Script Generation Challenge**: Auto-generated scripts don't know what structure to expect
4. **Error Handling Complexity**: Defensive coding patterns must handle multiple response formats
5. **User Experience**: Developers must manually explore tool responses before building solutions

### Why This Matters

In this project's progressive disclosure pattern:
- Agents need to write scripts that call MCP tools
- Without knowing output schemas, agents must write defensive code with multiple fallback patterns
- This adds complexity, reduces code clarity, and increases token usage
- Makes it harder to auto-generate reliable type-safe wrappers

The result: approximately 50-60% of MCP servers in the wild don't provide output schemas, forcing client implementations to choose between:
- **Option A**: Accept untyped responses and hope for the best
- **Option B**: Implement expensive schema inference by executing tools
- **Option C**: Require manual server-specific handling

## Overview
This document clarifies how the Model Context Protocol (MCP) exposes tool capabilities to LLMs and addresses the optional nature of output schemas in the specification.

## How MCP Servers Expose Capabilities

### 1. Tool Discovery via `list_tools()`
MCP servers provide a standardized way for clients to discover available tools:

- **Endpoint**: `list_tools()` - Returns a list of all available tools
- **Implementation**: `src/runtime/mcp_client.py:260`
  ```python
  result = await client.list_tools()
  tools = result.tools if hasattr(result, "tools") else []
  ```

### 2. Tool Schema Information
Each tool in MCP provides the following metadata:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier (e.g., "git_status", "fetch") |
| `description` | No | Human-readable description of what the tool does |
| `inputSchema` | **Yes** | JSON Schema defining the tool's parameters |
| `outputSchema` | No | JSON Schema defining the tool's output structure |

### 3. MCP Tool Type Definition
From `.venv/lib/python3.11/site-packages/mcp/types.py:871-881`:

```python
class Tool(BaseMetadata):
    """Definition for a tool the client can call."""

    description: str | None = None
    """A human-readable description of the tool."""

    inputSchema: dict[str, Any]
    """A JSON Schema object defining the expected parameters for the tool."""

    outputSchema: dict[str, Any] | None = None
    """
    An optional JSON Schema object defining the structure of the tool's output
    returned in the structuredContent field of a CallToolResult.
    """
```

## The Output Schema Problem

### Key Finding: Output Schemas are OPTIONAL
- **`inputSchema`** is REQUIRED - Every tool must define its input parameters
- **`outputSchema`** is OPTIONAL (`None` by default) - Tools may or may not define their output structure

### Why Output Schemas are Often Missing
From `.claude/agents/developer.md:286`:
> "Many MCP servers don't provide `outputSchema` in their tool definitions because the underlying REST APIs lack formal schemas."

This reflects real-world constraints where many APIs and tools don't have formal response schemas.

## Current State: How This Project Copes

This repository employs **8 distinct but complementary strategies** to cope with missing output schemas, forming a multi-layered defense against uncertainty.

### Strategy 1: Input-Only Fallback (`generate_wrappers.py`)
When generating tool wrappers:
- **Input schemas**: Generate precise Pydantic `ParamsModel` classes
- **Output schemas**: Missing? Return generic `Dict[str, Any]`
- **Location**: `src/runtime/generate_wrappers.py:86-112`

The wrapper functions include defensive unwrapping and field normalization built-in (lines 74-80):
```python
# Defensive unwrapping
unwrapped = getattr(result, "value", result)

# Apply field normalization
normalized = normalize_field_names(unwrapped, "{server_name}")

return normalized
```

### Strategy 2: Type Conversion Resilience (`schema_utils.py`)
Every JSON Schema to Python type conversion has fallback paths:
- **Primitive types**: Direct mapping (`str`, `int`, `float`, `bool`)
- **Union types**: Handle nullability (`["string", "null"]` → `Optional[str]`)
- **Unknown objects**: Fallback to `Dict[str, Any]`
- **Unrecognized types**: Fallback to `Any`
- **Location**: `src/runtime/schema_utils.py`

Philosophy: "Better approximate than crash" - gracefully degrade type specificity

### Strategy 3: Runtime Type Inference (`schema_inference.py`)
Infer types from actual API responses when schemas unavailable:
- **Primitives**: Detect `str`, `int`, `float`, `bool` from values
- **Collections**: Infer `List[T]`, `Dict[str, V]` with homogeneous type detection
- **Empty collections**: Fallback to `List[Any]`, `Dict[str, Any]`
- **Mixed types**: Conservative fallback to `Any`
- **ALL FIELDS MARKED OPTIONAL** for defensive coding
- **Location**: `src/runtime/schema_inference.py`

Generated code includes warning header:
```python
"""
WARNING: These models are inferred from actual API responses.
They may be incomplete or incorrect. Use with caution.
All fields are Optional for defensive coding.
"""
```

### Strategy 4: Safe Tool Execution Discovery (`discover_schemas.py`)
Execute harmless read-only tools to learn real output structure:
- Configure "safe tools" via `discovery_config.json` with sample parameters
- Execute each tool with minimal parameters
- Infer Pydantic models from actual responses
- Error tolerance: tool failures don't stop discovery (line 95-98)
- Write inferred models to `servers/{server}/discovered_types.py`
- **Location**: `src/runtime/discover_schemas.py`

Pattern: "Understand by executing safely" - learn schemas from actual behavior

### Strategy 5: Field Name Normalization (`normalize_fields.py`)
Handle inconsistent API field casing across different servers:
- **ADO (Azure DevOps)**: `system.* → System.*`, `custom.* → Custom.*`
- **GitHub/Filesystem**: No normalization needed
- **Recursive handling**: Normalizes nested structures deeply
- **Immutability**: Never modifies originals, creates new objects
- **Applied automatically**: Generated wrappers include normalization (line 78)
- **Location**: `src/runtime/normalize_fields.py`

Pattern: "Normalize after extraction" - post-process to handle API inconsistencies

### Strategy 6: Graceful Error Handling (`harness.py`)
Robust script execution with cascading error isolation:
- **Signal handling**: SIGINT/SIGTERM shutdown (lines 74-81)
- **Exception isolation**: Separate handling for `KeyboardInterrupt` vs general exceptions
- **Always cleanup**: Try/finally ensures cleanup runs even on failure
- **Graceful suppression**: Ignores `BaseExceptionGroup` errors in cleanup context
- **Location**: `src/runtime/harness.py`

Philosophy: "Fail gracefully, always cleanup" - exceptions never prevent teardown

### Strategy 7: Multi-Layer Defensive Unwrapping (`mcp_client.py`)
Try multiple strategies to extract actual result from MCP response:
- **Try 1**: `result.value` (most common format)
- **Try 2**: `result.content` (alternative response format)
- **Try 3**: Fall back to raw `result` object
- **Try 4**: For text responses, attempt JSON parsing
- **Location**: `src/runtime/mcp_client.py:342-371`

Full unwrapping strategy:
```python
result = await client.call_tool(tool_name, params)

# Try multiple unwrapping strategies
if hasattr(result, "value"):
    unwrapped = result.value
elif hasattr(result, "content"):
    unwrapped = result.content
else:
    unwrapped = result

# Handle text responses with potential JSON
if isinstance(unwrapped, list) and len(unwrapped) > 0:
    first_item = unwrapped[0]
    if hasattr(first_item, "text"):
        text_content = first_item.text
        if isinstance(text_content, str) and text_content.strip().startswith(("{", "[")):
            try:
                return json.loads(text_content)
            except json.JSONDecodeError:
                return text_content
        return text_content

return unwrapped
```

Philosophy: "Defense in depth" - multiple fallback strategies at each point

### Strategy 8: Defensive Optionality (All Modules)
All inferred fields marked as `Optional` to acknowledge uncertainty:
- Fields without explicit `required` list treated as optional
- Inferred models use `Optional[T]` for all fields
- Generated docstrings warn about inference limitations
- Test coverage validates all fallback paths
- **Test files**: `tests/unit/test_schema_inference.py`, `tests/unit/test_mcp_client.py:371-498`

Philosophy: "Admit what you don't know" - use `Optional` as an honest type annotation

### Integration: The Full Pipeline

These 8 strategies work together in sequence:

```
Tool Definition (missing outputSchema)
    ↓
Generate Wrapper with Params Model + Dict[str, Any] return
    ↓
Script calls wrapper → MCP tool executes
    ↓
Multi-layer unwrapping (try .value, .content, raw)
    ↓
Field normalization (handle API inconsistencies)
    ↓
Return Dict[str, Any] with defensive Optional types
    ↓
Script receives untyped data, handles with defensive patterns
    ↓
Optional: Infer schema for future use (discover_schemas.py)
```

### Test Coverage Strategy
Comprehensive tests verify all fallback paths work:
- **test_schema_inference.py**: Runtime type inference edge cases
- **test_discover_schemas_mock.py**: Schema discovery robustness and error tolerance
- **test_mcp_client.py (TestDefensiveUnwrapping)**: All unwrapping strategies (lines 371-498)
- **test_normalize_fields.py**: Field normalization nested structures
- **test_generate_wrappers.py**: Schema conversion with missing fields

All tests explicitly validate fallback behavior - not just happy paths.

## MCP Server-Side Validation

When an output schema IS provided, the MCP server validates automatically (`.venv/lib/python3.11/site-packages/mcp/server/lowlevel/server.py`):
- If `outputSchema` is defined but no structured output is returned → Error
- If structured output is provided → Validates against the schema using jsonschema

## Design Philosophy

The MCP protocol is designed for **model-controlled execution**:
- LLMs can automatically discover and invoke tools based on provided metadata
- Servers act as capability providers, advertising what they can do through structured schemas
- The optional nature of output schemas makes MCP flexible enough to work with both:
  - Well-defined tools with strict schemas
  - Legacy APIs without formal response definitions

## Progressive Disclosure Pattern Benefits

This project leverages MCP's capability exposure to achieve ~98.7% token reduction:
1. Agent explores `./servers/` to discover available tools (minimal tokens)
2. Agent reads only needed tool definitions (targeted loading)
3. Agent writes Python script that processes data locally
4. Script returns summary only (not raw data)

The optional output schema actually enables this pattern - if all tools required strict output schemas, many real-world integrations wouldn't be possible.

## Recommendations

1. **For MCP Server Developers**:
   - Always provide `outputSchema` when possible for better type safety
   - Document response structures in tool descriptions when schemas aren't feasible

2. **For MCP Client Developers**:
   - Always use defensive coding patterns
   - Implement progressive discovery for unknown response structures
   - Consider schema inference tools for frequently-used servers

3. **For the MCP Specification**:
   - The optional output schema is a pragmatic choice that enables wider adoption
   - Consider standardizing common response patterns even without full schemas