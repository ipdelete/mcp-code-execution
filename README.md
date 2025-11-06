# MCP Code Execution Implementation

Implementation of the code execution pattern for Model Context Protocol (MCP) as described in Anthropic's article: [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp).

> This approach addresses key challenges in scaling MCP agents: tool definitions that overload context windows, and intermediate results that consume excessive tokens. By presenting MCP servers as importable TypeScript modules, agents can load only what they need and process data locally before returning results.

## What This Is

Instead of loading all MCP tool definitions into context and passing intermediate results through the model, this project presents MCP servers as TypeScript modules that can be imported and executed in code. This enables:

- **Progressive Tool Loading** - Import only the tools you need
- **Efficient Data Processing** - Handle large datasets without passing through context
- **Privacy Preservation** - Intermediate results stay in execution environment
- **State Persistence** - Save results and build reusable skills

## How It Works

This repository provides TypeScript wrapper modules for MCP servers that AI agents can import and use in generated code. The agent harness intercepts these calls and executes the actual MCP protocol communication.

**For AI Agents:**
1. Review the prompt in `prompts/01-basic-search-and-analyze.md`
2. Write TypeScript code that imports from `./servers/github-mcp`
3. The harness intercepts `callMcpTool()` and executes the MCP protocol
4. Results are processed locally and only summaries return to context

## Quick Start

**For Users:** Provide this prompt to an AI agent with access to GitHub Copilot or similar MCP-enabled environment:

```
Create a TypeScript script at workspace/search-and-analyze.ts that imports 
from ./servers/github-mcp, searches for TypeScript files with "MCP" in the 
modelcontextprotocol/servers repo, processes the results to find total files, 
top 3 directories, and average score. Save full results to workspace/mcp-files.json 
and console.log only the summary.
```

**What the agent will generate:**

```typescript
import * as github from '../servers/github-mcp';
import * as fs from 'fs/promises';

async function main() {
  // Agent writes code that calls MCP tools
  const results = await github.search_code({
    query: 'MCP language:typescript repo:modelcontextprotocol/servers',
    perPage: 100
  });

  // Process results locally (data never goes through model context)
  const directories = results.items.map(item => 
    item.path.substring(0, item.path.lastIndexOf('/'))
  );

  const dirCounts = directories.reduce((acc, dir) => {
    acc[dir] = (acc[dir] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const topDirectories = Object.entries(dirCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([dir]) => dir);

  const averageScore = results.items.reduce((sum, item) => 
    sum + item.score, 0) / results.items.length;

  // Save full results to disk
  await fs.writeFile(
    './workspace/mcp-files.json', 
    JSON.stringify(results, null, 2)
  );

  // Return only summary to context
  console.log(JSON.stringify({
    totalFiles: results.items.length,
    topDirectories,
    averageScore
  }, null, 2));
}

main();
```

**Result:** Only ~100 bytes of summary flow through context, while 5KB+ of full results stay in the execution environment.

## Project Structure

```
.
├── docs/                    # Documentation
├── prompts/                # Prompt examples for AI agents
│   └── 01-basic-search-and-analyze.md
├── servers/                # MCP server TypeScript wrappers
│   ├── github-mcp/         # GitHub MCP server tools
│   │   ├── search_code.ts  # Code search
│   │   ├── get_file_contents.ts
│   │   └── index.ts        # Exported API
│   └── mcp-client.ts       # Core MCP client (intercepted by harness)
└── workspace/              # Execution environment for generated scripts
```

## For Developers

To use this pattern in your own agent harness:

1. **Setup**
   ```bash
   npm install
   ```

2. **Intercept `callMcpTool`**
   - Hook into TypeScript execution environment
   - Intercept calls to `callMcpTool()` in `servers/mcp-client.ts`
   - Translate to MCP protocol requests
   - Return results to executing code

3. **Add MCP Servers**
   - Create directory: `servers/your-server/`
   - Wrap tools as TypeScript functions calling `callMcpTool()`
   - Export from `index.ts`

The traditional approach loads all tools upfront:
```typescript
// ❌ All tool definitions in context
// ❌ All intermediate results through model
TOOL CALL: gdrive.getDocument() → [50KB transcript]
TOOL CALL: salesforce.update(notes: "[paste 50KB again]")
```

This implementation uses code execution:
```typescript
// ✅ Import only what you need
import * as gdrive from './servers/google-drive';
import * as salesforce from './servers/salesforce';

// ✅ Data flows through code, not context
const doc = await gdrive.getDocument({ id: 'abc123' });
await salesforce.updateRecord({ 
  objectType: 'Lead',
  data: { Notes: doc.content }  // No re-serialization
});
console.log('Updated'); // Only this goes to context
```

## Documentation

- [Anthropic Article: Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) - Original article
- [Article Copy](./docs/code-execution-with-mcp.md) - Local copy for reference
- [Prompt Examples](./prompts/) - Example prompts for AI agents
- [Server Implementation](./servers/README.md) - How wrappers work

## Contributing

To add support for additional MCP servers:
1. Create a directory under `servers/`
2. Wrap each tool as a TypeScript function
3. Call `callMcpTool()` with server name, tool name, and params
4. Export from `index.ts`

## License

MIT
