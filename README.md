# MCP Code Execution Implementation

**Working implementation** of the code execution pattern for Model Context Protocol (MCP) as described in Anthropic's article: [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp).

> This approach addresses key challenges in scaling MCP agents: tool definitions that overload context windows, and intermediate results that consume excessive tokens. By presenting MCP servers as importable TypeScript modules, agents can load only what they need and process data locally before returning results.

## What This Is

A fully functional implementation that allows you to write TypeScript code that imports MCP tools as modules. Instead of loading all MCP tool definitions into context and passing intermediate results through the model, this project:

- **Connects to real MCP servers** via the official MCP SDK
- **Presents tools as importable TypeScript modules** that agents can use naturally
- **Intercepts calls** and routes them to actual MCP protocol communication
- **Processes data locally** keeping intermediate results out of model context

### Benefits

- **Progressive Tool Loading** - Import only the tools you need (98%+ token reduction)
- **Efficient Data Processing** - Handle large datasets without passing through context
- **Privacy Preservation** - Intermediate results stay in execution environment
- **State Persistence** - Save results and build reusable skills
- **Type Safety** - Full TypeScript support with IntelliSense

## How It Works

1. **Write TypeScript code** that imports MCP tools as modules
2. **Run with harness**: `npm run exec workspace/your-script.ts`
3. **Harness intercepts** `callMcpTool()` calls
4. **Real MCP communication** happens via stdio transport to actual MCP servers
5. **Results flow back** to your code as if calling a normal async function

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-code-execution.git
cd mcp-code-execution

# Install dependencies
npm install
```

### Configuration

Edit `mcp-config.json` to configure which MCP servers to connect to:

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

### Run the Example

```bash
npm run exec workspace/example-data-processing.ts
```

**Output:**
```
=== Summary (only this flows through model context) ===
{
  "totalItems": 131,
  "fileCount": 125,
  "directoryCount": 6,
  "dataSize": "5.65 KB",
  "savedTo": "workspace/directory-listing.json"
}

✅ Pattern demonstration complete!

Context savings:
  - Raw data size: 5.65 KB
  - Summary size: 445 bytes
  - Reduction: 92.3%
```

## Writing Your Own Scripts

Create a TypeScript file in the `workspace/` directory:

```typescript
// workspace/my-script.ts
import { callMcpTool } from '../servers/mcp-client';

async function main() {
  // Call MCP tools using the serverName__toolName format
  const result = await callMcpTool('filesystem__list_directory', {
    path: '/private/tmp'
  });

  // Process data locally - it never enters model context!
  const lines = result.split('\n').filter(line => line.trim());
  const fileCount = lines.filter(l => l.startsWith('[FILE]')).length;

  // Only the summary flows through context
  console.log({ totalLines: lines.length, fileCount });
}

main();
```

**Run it:**
```bash
npm run exec workspace/my-script.ts
```

### Available Tool Wrappers

The project includes TypeScript wrappers that provide a cleaner API:

```typescript
// Using the wrapper (recommended)
import * as github from '../servers/github-mcp';

const results = await github.search_code({
  query: 'language:typescript',
  perPage: 10
});

// Or call MCP tools directly
import { callMcpTool } from '../servers/mcp-client';

const results = await callMcpTool('github__search_code', {
  query: 'language:typescript',
  perPage: 10
});
```

## Project Structure

```
.
├── docs/                           # Documentation
├── mcp-config.json                 # MCP server configuration
├── prompts/                        # Prompt examples for AI agents
├── runtime/                        # Execution harness
│   ├── harness.ts                  # Main harness entry point
│   ├── mcp-client-impl.ts          # Real MCP client implementation
│   └── mcp-client-shim.ts          # Module shim for interception
├── servers/                        # MCP server TypeScript wrappers
│   ├── github-mcp/                 # GitHub MCP server tools
│   │   ├── search_code.ts          # Code search wrapper
│   │   ├── get_file_contents.ts    # File access wrapper
│   │   └── index.ts                # Public API
│   └── mcp-client.ts               # Stub (replaced at runtime)
└── workspace/                      # Your scripts go here
    ├── example-data-processing.ts  # Complete example
    └── test-filesystem.ts          # Simple test
```

## Architecture

### How Interception Works

1. **You write code** that imports from `servers/mcp-client.ts`
2. **At runtime**, the harness sets `MCP_HARNESS_ACTIVE=true`
3. **When callMcpTool is called**, it detects the environment variable
4. **It dynamically imports** the real implementation from `runtime/mcp-client-impl.ts`
5. **The real implementation** connects to MCP servers via stdio
6. **Results flow back** to your code transparently

### For Developers

**Adding new MCP servers:**

1. Add to `mcp-config.json`:
   ```json
   {
     "mcpServers": {
       "your-server": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-yourserver"]
       }
     }
   }
   ```

2. Create wrappers in `servers/your-server/`:
   ```typescript
   // servers/your-server/your_tool.ts
   import { callMcpTool } from '../mcp-client';

   export async function your_tool(params: YourParams) {
     return callMcpTool('your-server__your_tool', params);
   }
   ```

3. Export from `servers/your-server/index.ts`

## Comparison: Traditional vs Code Execution

### Traditional Approach (❌ Inefficient)

```typescript
// All 40 MCP servers' tool definitions loaded into context: ~150KB
// Every intermediate result flows through model

TOOL CALL: filesystem__list_directory("/tmp")
  → Returns 5.65 KB of file listings
  → ALL 5.65 KB enters model context

TOOL CALL: process_results(...)
  → Model processes 5.65 KB
  → Returns summary

Total context: ~155 KB
```

### Code Execution Approach (✅ Efficient)

```typescript
// Import only what you need: ~1 KB
import { callMcpTool } from '../servers/mcp-client';

// Data stays in execution environment
const listing = await callMcpTool('filesystem__list_directory', {
  path: '/tmp'
}); // 5.65 KB stays here

// Process locally
const summary = processLocally(listing); // Still local

// Only summary to context
console.log(summary); // 445 bytes

Total context: ~1.4 KB (92.3% reduction!)
```

### Real-World Example

From our filesystem example:
- **Raw data:** 5.65 KB
- **Summary:** 445 bytes
- **Savings:** 92.3%

From the article's Google Drive → Salesforce example:
- **Raw data:** 150 KB (tool defs + transcript)
- **Summary:** 2 KB
- **Savings:** 98.7%

## Technical Details

### MCP Protocol

This implementation uses:
- **[@modelcontextprotocol/sdk](https://www.npmjs.com/package/@modelcontextprotocol/sdk)** - Official MCP TypeScript SDK
- **stdio transport** - Communicates with MCP servers via stdin/stdout
- **Tool calling** - Implements the MCP tools/call protocol

### Tool Identifier Format

Tools are identified using the pattern: `serverName__toolName`

Examples:
- `filesystem__list_directory`
- `github__search_code`
- `salesforce__update_record`

This matches the article's pattern and makes it easy to route calls to the correct server.

## Troubleshooting

**"callMcpTool was not intercepted by agent harness"**
- Make sure you're running with `npm run exec`, not directly with `npx tsx`
- The harness sets the required environment variable for interception

**"Connection closed" errors**
- Check that the MCP server command in `mcp-config.json` is correct
- Verify the server is installed: `npx -y @modelcontextprotocol/server-filesystem --help`

**Path access denied errors**
- For filesystem server, ensure paths are within allowed directories
- On macOS, use `/private/tmp` instead of `/tmp`

## Examples

- `workspace/test-filesystem.ts` - Simple filesystem test
- `workspace/example-data-processing.ts` - Full pattern demonstration
- `workspace/test-list-tools.ts` - List all available MCP tools
- `prompts/01-basic-search-and-analyze.md` - Prompt for AI agents

## Documentation

- [Anthropic Article: Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) - Original article
- [Article Copy](./docs/code-execution-with-mcp.md) - Local copy for reference
- [Prompt Examples](./prompts/) - Example prompts for AI agents
- [Server Implementation](./servers/README.md) - How wrappers work

## Contributing

Contributions are welcome! To add support for additional MCP servers:

1. Add server configuration to `mcp-config.json`
2. Create directory under `servers/your-server/`
3. Wrap each tool as a TypeScript function calling `callMcpTool('server__tool', params)`
4. Export from `servers/your-server/index.ts`
5. Add documentation and examples

## References

- [Model Context Protocol](https://modelcontextprotocol.io/) - Official MCP documentation
- [MCP Servers](https://github.com/modelcontextprotocol/servers) - Official MCP server implementations
- [Claude Code](https://claude.ai/code) - AI coding assistant with MCP support

## License

MIT
