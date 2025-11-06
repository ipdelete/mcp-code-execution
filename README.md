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

## How It Works: Progressive Disclosure

The key insight from the article is **progressive disclosure** - agents discover tools by exploring the filesystem, not loading everything upfront:

> "The agent discovers tools by exploring the filesystem: listing the `./servers/` directory to find available servers, then reading the specific tool files it needs to understand each tool's interface. This lets the agent load only the definitions it needs for the current task."

**In practice:**

1. **Agent explores filesystem** - Lists `./servers/` to discover available servers
2. **Agent reads only what it needs** - Reads specific tool files to understand interfaces
3. **Write code** - Imports and uses only the tools needed for the task
4. **Run with harness** - `npm run exec workspace/your-script.ts`
5. **Lazy loading** - MCP servers connect **on-demand** when first tool is called (not at startup!)
6. **Data stays local** - Process results in execution environment
7. **Return summary** - Only summary flows back to model context

**Token savings:** 150,000 → 2,000 tokens (98.7% reduction from the article)

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

### Run the Progressive Disclosure Example

This demonstrates the core pattern from the article:

```bash
npm run exec workspace/example-progressive-disclosure.ts
```

**Output:**
```
=== Progressive Disclosure Pattern ===

1. Discovering available MCP servers...
   Found 1 servers: github-mcp
   📁 All discovered by reading filesystem, not loaded into context!

2. Task: List files in a directory
   Decision: Need filesystem operations → use "filesystem" server

3. Reading tool definition to understand interface...
   Only reading what we need for this task (not loading all 26 GitHub tools!)

4. Importing only the filesystem server...
   ⚠️  Server will connect on-demand when we call first tool

5. Calling tool (server connects NOW, not at startup)...
[MCP] Connecting to server on-demand: filesystem

=== Summary (only this goes to model context) ===
{
  "totalItems": 131,
  "serverUsed": "filesystem",
  "serversConnected": 1,
  "tokensUsed": "~2,000 (only read 1 tool definition)",
  "tokensIfTraditional": "~150,000 (all tools loaded upfront)"
}

✅ Progressive disclosure complete!

From the article:
  "This reduces token usage from 150,000 to 2,000 tokens"
  "A time and cost saving of 98.7%"
```

## Writing Your Own Scripts

The pattern: **Discover → Read → Use → Process → Summarize**

```typescript
// workspace/my-script.ts
import * as fs from 'fs/promises';
import * as path from 'path';

async function main() {
  // 1. DISCOVER: Explore filesystem to find available servers
  const servers = await fs.readdir(path.join(process.cwd(), 'servers'), {
    withFileTypes: true
  });
  const availableServers = servers
    .filter(e => e.isDirectory())
    .map(e => e.name);
  console.log(`Available servers: ${availableServers.join(', ')}`);

  // 2. READ: Read only the tool definitions you need
  // (Agent can read tool files to understand interfaces)

  // 3. USE: Import and call only what you need
  const { callMcpTool } = await import('../servers/mcp-client');

  // Server connects on-demand here!
  const result = await callMcpTool('filesystem__list_directory', {
    path: '/private/tmp'
  });

  // 4. PROCESS: Data stays local - never enters model context
  const lines = result.split('\n').filter(line => line.trim());
  const fileCount = lines.filter(l => l.startsWith('[FILE]')).length;

  // 5. SUMMARIZE: Only summary flows through context
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
│   ├── harness.ts                  # Main harness (sets env var, runs scripts)
│   └── mcp-client-impl.ts          # Real MCP client implementation
├── servers/                        # MCP server TypeScript wrappers
│   ├── github-mcp/                 # GitHub MCP server tools
│   │   ├── search_code.ts          # Code search wrapper
│   │   ├── get_file_contents.ts    # File access wrapper
│   │   └── index.ts                # Public API
│   └── mcp-client.ts               # Stub (routes to impl at runtime)
└── workspace/                      # Your scripts go here
    ├── example-data-processing.ts  # Complete example
    └── test-filesystem.ts          # Simple test
```

## Architecture

### How It Works

The implementation uses **environment variable routing** instead of module interception:

1. **Agent explores filesystem** - Reads `./servers/` to discover available servers
2. **Agent reads tool definitions** - Opens specific tool files to understand interfaces
3. **Agent writes code** - Imports from `servers/mcp-client.ts` only what it needs
4. **Harness starts** - Sets `MCP_HARNESS_ACTIVE=true`, loads config (no connections yet!)
5. **First tool call** - `callMcpTool()` checks env var, dynamically imports real implementation
6. **Lazy connection** - Server connects **on-demand** via stdio when first tool is called
7. **Results flow back** - Returned to your code as normal function results
8. **Process locally** - Data never enters model context
9. **Return summary** - Only summary flows back to model

**Key insights:**
- No module interception needed - just env var check + dynamic import
- Nothing loads upfront! Agents discover by reading files, servers connect on-demand
- The stub in `servers/mcp-client.ts` does the routing automatically

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

## Comparison: Traditional vs Code Execution with Progressive Disclosure

### Traditional Approach (❌ Inefficient)

```typescript
// AT STARTUP: Load all 40 MCP servers' tool definitions
// → 150,000 tokens for tool definitions alone!

TOOL CALL: filesystem__list_directory("/tmp")
  → Returns 5.65 KB of file listings
  → ALL 5.65 KB enters model context

TOOL CALL: process_results(...)
  → Model processes 5.65 KB
  → Returns summary

Total context: ~150 KB tool defs + 5.65 KB data = ~155 KB
```

### Code Execution with Progressive Disclosure (✅ Efficient)

```typescript
// AT STARTUP: Nothing loaded! Config file read, but no connections.

// STEP 1: Agent explores filesystem (progressive disclosure)
const servers = fs.readdirSync('./servers'); // ['github-mcp', ...]
// Agent sees what's available WITHOUT loading definitions

// STEP 2: Agent reads ONLY the tool file it needs
const toolCode = fs.readFileSync('./servers/filesystem/list_directory.ts');
// ~100 bytes read, understands interface

// STEP 3: Agent uses it
import { callMcpTool } from '../servers/mcp-client';

// Server connects ON-DEMAND here (not at startup!)
const listing = await callMcpTool('filesystem__list_directory', {
  path: '/tmp'
}); // 5.65 KB stays in execution environment

// STEP 4: Process locally
const summary = processLocally(listing); // Data never enters context

// STEP 5: Only summary to context
console.log(summary); // 445 bytes

Total context: ~2 KB (only 1 tool definition read + summary)
```

### Token Savings

**From our progressive disclosure example:**
- **Traditional:** ~150,000 tokens (all tool definitions loaded)
- **Code execution:** ~2,000 tokens (only read 1 tool definition)
- **Reduction:** 98.7% (matches the article exactly!)

**Why such massive savings?**
1. **No upfront loading** - Tools discovered by filesystem exploration
2. **Lazy loading** - Servers connect on-demand, not at startup
3. **Local processing** - Data never enters model context
4. **Progressive disclosure** - Read only what you need, when you need it

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

**"callMcpTool requires the MCP harness to be active"**
- Make sure you're running with `npm run exec`, not directly with `npx tsx`
- The harness sets `MCP_HARNESS_ACTIVE=true` which the stub checks to route calls
- The stub automatically imports the real implementation when the env var is set

**"Connection closed" errors**
- Check that the MCP server command in `mcp-config.json` is correct
- Verify the server is installed: `npx -y @modelcontextprotocol/server-filesystem --help`

**Path access denied errors**
- For filesystem server, ensure paths are within allowed directories
- On macOS, use `/private/tmp` instead of `/tmp`

## Examples

**Progressive Disclosure (Core Pattern from Article):**
- `workspace/example-progressive-disclosure.ts` - **START HERE** - Shows filesystem discovery, lazy loading, 98.7% token reduction

**Additional Examples:**
- `workspace/example-data-processing.ts` - Data processing with local filtering
- `workspace/test-filesystem.ts` - Simple filesystem test
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
