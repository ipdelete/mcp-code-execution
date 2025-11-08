# Python Port - Differences from TypeScript

This document outlines key differences between the Python and TypeScript implementations.

## Architecture Decisions

| Aspect | TypeScript | Python | Rationale |
|--------|-----------|--------|-----------|
| Package Manager | npm/pnpm | uv | Modern, fast Python tooling |
| Type System | TypeScript | Pydantic | Runtime validation + serialization |
| Async | Promises/async-await | asyncio | Native Python async |
| Path Handling | string paths | pathlib.Path | More Pythonic |
| Code Generation | Template literals | f-strings | Native Python |

## Type System Mapping

### Basic Types

| JSON Schema | TypeScript | Python |
|-------------|-----------|--------|
| `"string"` | `string` | `str` |
| `"number"` | `number` | `float` |
| `"integer"` | `number` | `int` |
| `"boolean"` | `boolean` | `bool` |
| `"null"` | `null` | `None` |

### Complex Types

| JSON Schema | TypeScript | Python |
|-------------|-----------|--------|
| `["string", "null"]` | `string \| null` | `Optional[str]` |
| `{type: "array"}` | `Array<T>` | `List[T]` |
| `{enum: [...]}` | `enum` or union | `Literal[...]` |
| `{additionalProperties}` | `Record<string, T>` | `Dict[str, T]` |

## API Differences

### Initialization

**TypeScript**:
```typescript
const manager = getMcpClientManager();
await manager.initialize();
```

**Python**:
```python
manager = get_mcp_client_manager()
await manager.initialize()
```

### Tool Calling

**TypeScript**:
```typescript
const result = await callMcpTool("git__git_status", { repo_path: "." });
```

**Python**:
```python
result = await call_mcp_tool("git__git_status", {"repo_path": "."})
```

## Pattern Preservation

Both implementations preserve the core 98.7% token reduction pattern:

✅ Lazy initialization
✅ Lazy connection
✅ Tool caching
✅ Defensive unwrapping
✅ Progressive disclosure

## Migration Guide

### Converting TypeScript Scripts to Python

1. **Imports**:
```typescript
// TypeScript
import { callMcpTool } from './runtime/mcp-client';
```

```python
# Python
from runtime.mcp_client import call_mcp_tool
```

2. **Async Execution**:
```typescript
// TypeScript
await main();
```

```python
# Python
import asyncio
asyncio.run(main())
```

3. **Tool Calls**:
```typescript
// TypeScript (camelCase)
const result = await callMcpTool("server__tool", { repoPath: "." });
```

```python
# Python (snake_case)
result = await call_mcp_tool("server__tool", {"repo_path": "."})
```
