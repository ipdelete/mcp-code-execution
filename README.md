# MCP Code Execution Implementation

Implementation of the code execution pattern for Model Context Protocol (MCP) as described in Anthropic's article: [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp).

> This approach addresses key challenges in scaling MCP agents: tool definitions that overload context windows, and intermediate results that consume excessive tokens. By presenting MCP servers as importable TypeScript modules, agents can load only what they need and process data locally before returning results.

## What This Is

Instead of loading all MCP tool definitions into context and passing intermediate results through the model, this project presents MCP servers as TypeScript modules that can be imported and executed in code. This enables:

- **Progressive Tool Loading** - Import only the tools you need
- **Efficient Data Processing** - Handle large datasets without passing through context
- **Privacy Preservation** - Intermediate results stay in execution environment
- **State Persistence** - Save results and build reusable skills

## Setup

```bash
npm install
```

## Project Structure

```
.
├── docs/                    # Documentation
├── prompts/                # Example use cases
├── servers/                # MCP server TypeScript wrappers
│   ├── github-mcp/         # GitHub MCP server tools
│   │   ├── search_code.ts  # Code search
│   │   ├── get_file_contents.ts
│   │   └── index.ts        # Exported API
│   └── mcp-client.ts       # Core MCP client
└── workspace/              # Execution environment for scripts
```

## Usage

### Import and Use MCP Tools

```typescript
import * as github from './servers/github-mcp';

// Search for code
const results = await github.search_code({
  query: 'MCP language:typescript repo:modelcontextprotocol/servers',
  perPage: 100
});

// Process results locally (not through context)
const directories = results.items.map(item => 
  item.path.substring(0, item.path.lastIndexOf('/'))
);

// Save to disk for later
await fs.writeFile('workspace/results.json', JSON.stringify(results));

// Return only summary
console.log({ totalFiles: results.items.length });
```

### Run Scripts

```bash
# Execute any TypeScript file
npm run dev <file.ts>

# Example
npm run dev workspace/search-and-analyze.ts

# Build
npm run build
```

## Key Pattern

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

- [Code Execution with MCP](./docs/code-execution-with-mcp.md) - Core concepts
- [Server Implementation](./servers/README.md) - How wrappers work

## Dependencies

- **TypeScript** - Type-safe tool wrappers
- **tsx** - Fast TypeScript execution
- **@types/node** - Node.js type definitions
