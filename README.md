# MCP Code Execution with Auto-Generated Wrappers

**Implementation of the code execution pattern for Model Context Protocol (MCP)** as described in [Anthropic's article](https://www.anthropic.com/engineering/code-execution-with-mcp), with **automatic TypeScript wrapper generation**.

> Reduces token usage from 150,000 → 2,000 tokens (98.7% reduction) through progressive disclosure and local data processing.

## What This Is

A TypeScript execution harness that:
- **Connects to MCP servers** via the official MCP SDK
- **Auto-generates typed wrappers** for all MCP tools
- **Enables progressive discovery** - agents explore the filesystem to find tools
- **Processes data locally** - keeps intermediate results out of context
- **Lazy loads servers** - connects on-demand when tools are first called

### Key Benefits

- **98.7% token reduction** - Load only the tools you need
- **Auto-generated types** - TypeScript interfaces from MCP schemas
- **Zero maintenance** - Wrappers stay in sync with servers
- **Privacy preservation** - Data stays in execution environment
- **Type safety** - Full IntelliSense support

## Quick Start

### 1. Install

```bash
git clone https://github.com/yourusername/mcp-code-execution.git
cd mcp-code-execution
npm install
```

### 2. Configure MCP Servers

Edit `mcp-config.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/private/tmp"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

### 3. Generate Wrappers

```bash
npm run generate
```

This auto-generates TypeScript wrappers for all configured servers:
- Connects to each MCP server
- Discovers available tools via `listTools()`
- Generates typed interfaces from JSON schemas
- Creates wrapper functions that call `callMcpTool()`

**Generated files** (in `servers/*/`):
```typescript
// servers/github/search_code.ts
import { callMcpTool } from '../../runtime/mcp-client';

interface SearchCodeParams {
  q: string;
  order?: 'asc' | 'desc';
  page?: number;
  per_page?: number;
}

interface SearchCodeResult {
  [key: string]: any;
}

/**
 * Search for code across GitHub repositories
 */
export async function search_code(params: SearchCodeParams): Promise<SearchCodeResult> {
  return await callMcpTool<SearchCodeResult>('github__search_code', params);
}
```

### 4. Run Example

```bash
npm run exec tests/example-progressive-disclosure.ts
```

## How It Works: Progressive Disclosure

The key insight is **progressive disclosure** - agents discover tools by exploring the filesystem:

1. **Agent explores** - Lists `./servers/` to find available servers
2. **Agent reads** - Reads specific tool files to understand interfaces
3. **Agent writes code** - Imports only the tools needed
4. **Harness executes** - Runs script with `npm run exec`
5. **Lazy loading** - Servers connect on-demand when first tool is called
6. **Data stays local** - Process results without passing through context
7. **Return summary** - Only summary goes back to model

**Token savings:** Load 1 tool definition instead of 40+ servers = 98.7% reduction

## Usage

### Write a Script

Create `tests/my-script.ts`:

```typescript
// 1. Import auto-generated wrappers
import { list_directory, read_text_file } from '../servers/filesystem';

async function main() {
  // 2. Call tools (server connects on-demand here!)
  const files = await list_directory({ path: '/private/tmp' });

  // 3. Process data locally (never enters model context)
  const fileCount = JSON.stringify(files).split('\n').length;

  // 4. Return only summary
  console.log({ totalFiles: fileCount });
}

main();
```

### Run It

```bash
npm run exec tests/my-script.ts
```

### Using Direct API

If you prefer, call MCP tools directly:

```typescript
import { callMcpTool } from '../runtime/mcp-client';

const result = await callMcpTool('github__search_code', {
  q: 'language:typescript MCP',
  per_page: 10
});
```

## Project Structure

```
.
├── mcp-config.json          # MCP server configuration
├── package.json             # Scripts: exec, generate
├── runtime/
│   ├── harness.ts           # Execution harness
│   ├── mcp-client.ts        # MCP client manager
│   └── generate-wrappers.ts # Auto-generation script
├── servers/                 # Auto-generated (gitignored)
│   ├── filesystem/          # Generated wrappers
│   └── github/              # Generated wrappers
└── tests/                   # Your scripts
```

## Architecture

### Execution Flow

```
1. npm run exec tests/script.ts
   ↓
2. Harness initializes (loads config, no connections)
   ↓
3. Script runs, imports wrappers
   ↓
4. First tool call → Server connects on-demand
   ↓
5. callMcpTool() → MCP client → Server (stdio)
   ↓
6. Result returns to script
   ↓
7. Script processes locally
   ↓
8. Only summary goes to console/context
```

### Key Components

**`runtime/harness.ts`**
- Initializes MCP client manager
- Runs TypeScript scripts with `tsx`
- Cleans up connections on exit

**`runtime/mcp-client.ts`**
- Manages MCP server connections
- Implements lazy loading
- Routes tool calls to correct servers

**`runtime/generate-wrappers.ts`**
- Connects to MCP servers
- Discovers tools via `listTools()`
- Converts JSON Schema → TypeScript types
- Generates wrapper functions

## Adding New Servers

### 1. Add to Config

```json
{
  "mcpServers": {
    "salesforce": {
      "command": "npx",
      "args": ["-y", "@your-org/mcp-server-salesforce"]
    }
  }
}
```

### 2. Generate Wrappers

```bash
npm run generate
```

That's it! Wrappers are automatically created.

### 3. Use It

```typescript
import { query_records } from '../servers/salesforce';

const contacts = await query_records({
  query: 'SELECT Id, Name FROM Contact LIMIT 10'
});
```

## Best Practices

### ✅ Keep Data Local

```typescript
// Good - Process locally, return summary
const files = await list_directory({ path: '/tmp' });
const count = JSON.stringify(files).split('\n').length;
console.log({ fileCount: count }); // ~50 bytes
```

### ❌ Avoid Passing Large Data to Context

```typescript
// Bad - Sends all data to context
const files = await list_directory({ path: '/tmp' });
console.log(files); // 5KB to context!
```

### Save Intermediate Results

```typescript
import * as fs from 'fs/promises';

// Fetch large dataset
const data = await search_code({ q: 'MCP', per_page: 100 });

// Save locally
await fs.writeFile('./data.json', JSON.stringify(data, null, 2));

// Return summary
console.log({ resultsFound: data.total_count });
```

## Comparison: Traditional vs Progressive Disclosure

### Traditional MCP (❌ Inefficient)

```
STARTUP: Load all 40 servers × ~4KB = 150KB of tool definitions
↓
CALL: filesystem__list_directory() → 5KB result enters context
↓
MODEL: Processes 5KB data, returns summary
↓
Total: 150KB + 5KB = 155KB in context
```

### Code Execution with Progressive Disclosure (✅ Efficient)

```
STARTUP: Load config only (no connections, no definitions)
↓
AGENT EXPLORES: ls ./servers → sees available servers
↓
AGENT READS: cat servers/filesystem/list_directory.ts (~100 bytes)
↓
CALL: list_directory() → Server connects on-demand → 5KB stays local
↓
PROCESS: Script filters locally (never enters context)
↓
RETURN: Summary only (~50 bytes)
↓
Total: ~2KB (1 tool definition + summary)
```

**Result:** 98.7% token reduction

## Regenerating Wrappers

Wrappers are gitignored and generated on-demand. To regenerate:

```bash
# Generate for all servers
npm run generate

# First-time setup on new clone
git clone <repo>
npm install
npm run generate
npm run exec tests/example-progressive-disclosure.ts
```

## Troubleshooting

**"MCP server not configured"**
- Check server name in `mcp-config.json` matches tool identifier
- Format: `serverName__toolName` (e.g., `filesystem__list_directory`)

**"Connection closed" errors**
- Verify MCP server is installed: `npx -y @modelcontextprotocol/server-filesystem --help`
- Check command and args in `mcp-config.json`

**Path access denied (filesystem server)**
- On macOS, use `/private/tmp` instead of `/tmp`
- Ensure path is in allowed directories (configured in `args`)

**Missing wrappers**
- Run `npm run generate` to create them

## References

- [Anthropic Article: Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) - Original article
- [Model Context Protocol](https://modelcontextprotocol.io/) - Official MCP docs
- [MCP Servers](https://github.com/modelcontextprotocol/servers) - Official server implementations
- [MCP SDK](https://www.npmjs.com/package/@modelcontextprotocol/sdk) - TypeScript SDK

## License

MIT
