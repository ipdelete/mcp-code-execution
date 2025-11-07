# CLAUDE.md

**Progressive disclosure MCP pattern**: Load tools on-demand (150k→2k tokens, 98.7% reduction). Lazy server connections, auto-gen TS wrappers, local data processing, filesystem tool discovery.

## Commands
- `npm run generate` - Gen TS wrappers from `mcp-config.json`
- `npm run exec <script.ts>` - Run script w/ MCP
- `npm run build` - Compile to `dist/`
- Example scripts: `tests/example-progressive-disclosure.ts`, `tests/test-generated-wrappers.ts`

## Core Files
- `runtime/mcp-client.ts` - `McpClientManager`: lazy loading, `initialize()` loads config only, `callTool()` connects on-demand, tool format `"serverName__toolName"`, singleton via `getMcpClientManager()`
- `runtime/harness.ts` - Exec harness: tsx registration, MCP init, cleanup
- `runtime/generate-wrappers.ts` - Auto-gen: connects all servers, introspects schemas, generates `servers/<server>/<tool>.ts` + `index.ts`

## Structure
`servers/` (gitignored, regen w/ `npm run generate`):
```
servers/<serverName>/<toolName>.ts  # Params interface, Result interface, async wrapper
servers/<serverName>/index.ts       # Exports all tools
```

`mcp-config.json` format:
```json
{"mcpServers": {"name": {"command": "npx", "args": ["-y", "pkg"], "env": {}}}}
```
Current: `MCP_DOCKER` via `docker mcp gateway run`

## Workflow
Add server: edit `mcp-config.json` → `npm run generate` → `import {tool} from '../servers/name'` → auto-connect on first call

Script pattern (`tests/`):
```typescript
import { callMcpTool } from '../runtime/mcp-client';
// Option 1: import {tool} from '../servers/name'; await tool(params);
// Option 2: await callMcpTool('name__tool', params);
// Process locally, log summaries only
```

## Key Details
- Tool ID: `"serverName__toolName"` (double underscore)
- Progressive disclosure: list `servers/` → read needed tools → lazy connect → local processing → summary only
- Type gen: handles primitives, enums, unions, nested objects, required/optional, JSDoc
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
