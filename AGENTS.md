# AGENTS.md

**Progressive disclosure MCP pattern**: Load tools on-demand (150k→2k tokens, 98.7% reduction). Lazy server connections, auto-gen Python wrappers, local data processing, filesystem tool discovery.

## Commands
- `uv run mcp-generate` - Gen Python wrappers from `mcp_config.json`
- `uv run mcp-discover` - Gen Pydantic types from actual API responses (see `discovery_config.json`)
- `uv run mcp-exec <script.py>` - Run script w/ MCP
- Example scripts: `workspace/example_progressive_disclosure.py`, `tests/integration/test_*.py`
- User scripts go in: `workspace/` (gitignored)

## Core Files
- `src/runtime/mcp_client.py` - `McpClientManager`: lazy loading, `initialize()` loads config only, `call_tool()` connects on-demand, tool format `"serverName__toolName"`, singleton via `get_mcp_client_manager()`
- `src/runtime/harness.py` - Exec harness: asyncio, MCP init, signal handlers, cleanup
- `src/runtime/generate_wrappers.py` - Auto-gen: connects all servers, introspects schemas, generates `servers/<server>/<tool>.py` + `__init__.py`
- `src/runtime/discover_schemas.py` - Schema discovery: calls safe read-only tools, generates `servers/<server>/discovered_types.py` from real responses
- `src/runtime/normalize_fields.py` - Field normalization: auto-converts inconsistent API field casing (e.g., ADO: `system.parent` → `System.Parent`)

## Structure
`servers/` (gitignored, regen w/ `uv run mcp-generate`):
```
servers/<serverName>/<toolName>.py         # Pydantic models, async wrapper
servers/<serverName>/__init__.py           # Barrel exports
servers/<serverName>/discovered_types.py   # Optional: Pydantic types from actual API responses
```

`mcp_config.json` format:
```json
{"mcpServers": {"name": {"command": "command", "args": ["arg1"], "env": {}}}}
```

`discovery_config.json` format (optional, for schema discovery):
```json
{"servers": {"name": {"safeTools": {"tool_name": {"param1": "value"}}}}}
```

## Workflow
Add server: edit `mcp_config.json` → `uv run mcp-generate` → `from servers.name import tool_name` → auto-connect on first call

Optional schema discovery: copy `discovery_config.example.json` → edit w/ safe read-only tools + real params → `uv run mcp-discover` → `from servers.name.discovered_types import ToolNameResult`

Script pattern (`workspace/` for user scripts, `tests/` for examples):
```python
from servers.name import tool_name
from servers.name.discovered_types import ToolNameResult  # optional

result = await tool_name(params)  # Pydantic model
# Use defensive coding: result.field or fallback
# Process locally, log summaries only
```

## Key Details
- Tool ID: `"serverName__toolName"` (double underscore)
- Progressive disclosure: list `servers/` → read needed tools → lazy connect → local processing → summary only
- Type gen: Pydantic models for all schemas, handles primitives, unions, nested objects, required/optional, docstrings
- Schema discovery: only use safe read-only tools (never mutations), types are hints (fields marked Optional), still use defensive coding
- Field normalization: auto-applied per server (e.g., ADO normalizes all fields to PascalCase for consistency)
- Python: asyncio for concurrency, Pydantic for validation, mypy for type safety, aiofiles for async file I/O

## Troubleshooting
- "MCP server not configured": check `mcp_config.json` keys
- "Connection closed": verify server command with `which <command>`
- Missing wrappers: `uv run mcp-generate`
- Import errors: ensure `src/` in sys.path (harness handles this)
- Type checking: `uv run mypy src/` for validation

## Refs
- [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [MCP spec](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
