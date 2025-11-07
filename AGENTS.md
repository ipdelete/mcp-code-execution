# AGENTS.md

**Progressive disclosure MCP pattern**: Load tools on-demand (150k→2k tokens, 98.7% reduction). Lazy server connections, auto-gen TS wrappers, local data processing, filesystem tool discovery.

## Commands
- `npm run generate` - Gen TS wrappers from `mcp-config.json`
- `npm run discover-schemas` - Gen TypeScript types from actual API responses (see `discovery-config.json`)
- `npm run exec <script.ts>` - Run script w/ MCP
- `npm run build` - Compile to `dist/`
- Example scripts: `tests/example-progressive-disclosure.ts`, `tests/test-generated-wrappers.ts`
- User scripts go in: `workspace/` (gitignored)

## Core Files
- `runtime/mcp-client.ts` - `McpClientManager`: lazy loading, `initialize()` loads config only, `callTool()` connects on-demand, tool format `"serverName__toolName"`, singleton via `getMcpClientManager()`
- `runtime/harness.ts` - Exec harness: tsx registration, MCP init, cleanup
- `runtime/generate-wrappers.ts` - Auto-gen: connects all servers, introspects schemas, generates `servers/<server>/<tool>.ts` + `index.ts`
- `runtime/discover-schemas.ts` - Schema discovery: calls safe read-only tools, generates `servers/<server>/discovered-types.ts` from real responses
- `runtime/normalize-fields.ts` - Field normalization: auto-converts inconsistent API field casing (e.g., ADO: `system.parent` → `System.Parent`)

## Structure
`servers/` (gitignored, regen w/ `npm run generate`):
```
servers/<serverName>/<toolName>.ts     # Params interface, Result interface, async wrapper
servers/<serverName>/index.ts          # Exports all tools
servers/<serverName>/discovered-types.ts  # Optional: TypeScript types from actual API responses
```

`mcp-config.json` format:
```json
{"mcpServers": {"name": {"command": "npx", "args": ["-y", "pkg"], "env": {}}}}
```

`discovery-config.json` format (optional, for schema discovery):
```json
{"servers": {"name": {"safeTools": {"tool_name": {"description": "...", "sampleParams": {...}}}}}}
```
Current: `ado` & `sequential-thinking` servers via Docker MCP Gateway

## Workflow
Add server: edit `mcp-config.json` → `npm run generate` → `import {tool} from '../servers/name'` → auto-connect on first call

Optional schema discovery: copy `discovery-config.example.json` → edit w/ safe read-only tools + real params → `npm run discover-schemas` → `import type {ToolResult} from '../servers/name/discovered-types'`

Script pattern (`workspace/` for user scripts, `tests/` for examples):
```typescript
import { tool_name } from '../servers/name';
import type { ToolNameResult } from '../servers/name/discovered-types'; // optional

const result = await tool_name(params) as ToolNameResult; // type hint
// Use defensive coding: result.field?.subfield || fallback
// Process locally, log summaries only
```

## Key Details
- Tool ID: `"serverName__toolName"` (double underscore)
- Progressive disclosure: list `servers/` → read needed tools → lazy connect → local processing → summary only
- Type gen: handles primitives, enums, unions, nested objects, required/optional, JSDoc
- Schema discovery: only use safe read-only tools (never mutations), types are hints (fields marked optional), still use defensive coding
- Field normalization: auto-applied per server (e.g., ADO normalizes all fields to PascalCase for consistency)
- CommonJS: `package.json` type, tsconfig module, `.js` imports for MCP SDK compat, tsx execution

## Troubleshooting
- "MCP server not configured": check `mcp-config.json` keys
- "Connection closed": verify `npx -y @pkg --help`
- Missing wrappers: `npm run generate`
- macOS paths: use `/private/tmp` not `/tmp`

## Refs
- [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [MCP spec](https://modelcontextprotocol.io/)
- [MCP SDK](https://github.com/modelcontextprotocol/typescript-sdk)
