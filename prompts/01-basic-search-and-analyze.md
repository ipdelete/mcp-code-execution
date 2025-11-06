# Prompt 1: Basic Search and Analyze

**Difficulty:** Beginner  
**Concept:** Learn how code execution keeps intermediate results out of context

## Your Task

Write a TypeScript script that:
1. Imports and uses the GitHub MCP server tools as a module
2. Searches for TypeScript files containing "MCP" in `modelcontextprotocol/servers` 
3. Processes results to find:
   - Total files found
   - Top 3 most common directory paths
   - Average score of results
4. Saves full results to `workspace/mcp-files.json`
5. Returns only the summary (not full results)

**Requirements:**
- Import from `./servers/github-mcp`
- Use TypeScript with proper types
- Process data using map/filter/reduce
- Write results to disk
- Console.log only the summary

## The Pattern

This demonstrates the code execution pattern from the article where:
- ✅ Import MCP tools as TypeScript modules (not load all definitions in context)
- ✅ Process data in execution environment (not through model context)
- ✅ Save intermediate results to disk
- ✅ Return only summary to context

## Why This Pattern?

Traditional approach (❌ inefficient):
```typescript
// All tool definitions loaded in context
TOOL CALL: search_code({ query: "..." })
→ [5KB of results flow through context]
TOOL CALL: process_results([5KB data passed again])
→ Summary returned
```

Code execution approach (✅ efficient):
```typescript
// Import only what you need
import * as github from './servers/github-mcp';

// Data processed in execution environment
const results = await github.search_code({ query: "..." });
const summary = processLocally(results); // 5KB stays here

// Only summary to context
console.log(summary); // 100 bytes
```

Benefits:
- **Progressive loading**: Import `github-mcp` only, not all MCP servers
- **Efficient data flow**: 5KB stays in execution, not in context  
- **Reusable code**: Save the script for future use

## Expected Output

A TypeScript file at `workspace/search-and-analyze.ts` containing:

```typescript
import * as github from '../servers/github-mcp';
import * as fs from 'fs/promises';

async function main() {
  // Call GitHub MCP server
  const results = await github.search_code({
    query: 'MCP language:typescript repo:modelcontextprotocol/servers',
    perPage: 100
  });

  // Extract directories (data stays in execution environment)
  const directories = results.items.map(item => 
    item.path.substring(0, item.path.lastIndexOf('/'))
  );

  // Count occurrences
  const dirCounts = directories.reduce((acc, dir) => {
    acc[dir] = (acc[dir] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Find top 3
  const topDirectories = Object.entries(dirCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([dir]) => dir);

  // Calculate average score
  const averageScore = results.items.reduce((sum, item) => 
    sum + item.score, 0) / results.items.length;

  // Save full results to disk
  await fs.writeFile(
    './workspace/mcp-files.json', 
    JSON.stringify(results, null, 2)
  );

  // Return only summary (this goes to context)
  const summary = {
    totalFiles: results.items.length,
    topDirectories,
    averageScore
  };
  
  console.log(JSON.stringify(summary, null, 2));
}

main();
```

When executed with `npm run dev workspace/search-and-analyze.ts`:
```json
{
  "totalFiles": 4,
  "topDirectories": [
    "src/everything",
    "src/filesystem", 
    "src/filesystem/__tests__"
  ],
  "averageScore": 1
}
```

The full 5KB+ result is saved to `workspace/mcp-files.json`, but only ~100 bytes of summary flow through context.

## How to Execute

Say to Copilot:
```
Create a TypeScript script at workspace/search-and-analyze.ts that imports 
from ./servers/github-mcp, searches for TypeScript files with "MCP" in the 
modelcontextprotocol/servers repo, processes the results to find total files, 
top 3 directories, and average score. Save full results to workspace/mcp-files.json 
and console.log only the summary.
```

Or directly:
```bash
npm run dev workspace/search-and-analyze.ts
```

## What Happens Behind the Scenes

When the agent harness executes your TypeScript code:

1. **Import is processed**
   ```typescript
   import * as github from '../servers/github-mcp';
   ```
   - Loads only the GitHub MCP wrapper module
   - Not all MCP servers, not all tool definitions
   
2. **Function call is intercepted**
   ```typescript
   const results = await github.search_code({ query: '...' });
   ```
   - Harness intercepts `callMcpTool()` before it executes
   - Harness translates to MCP protocol request
   - Harness sends to actual GitHub MCP server
   - Results returned as if function executed normally

3. **Data stays local**
   ```typescript
   const directories = results.items.map(...);
   await fs.writeFile('workspace/mcp-files.json', ...);
   ```
   - 5KB+ of data processed in execution environment
   - Never flows through model context
   - Saved to disk for later use

4. **Only summary to context**
   ```typescript
   console.log(JSON.stringify(summary));
   ```
   - ~100 bytes returned to model
   - 50x reduction in context consumption

From the article:
> "When the model writes code that imports and calls these functions, the agent 
> harness intercepts the calls and translates them into MCP tool requests behind 
> the scenes."

## Learning Objectives

- ✅ **Import pattern**: Use `import * as github from './servers/github-mcp'` not direct tool calls
- ✅ **Harness interception**: Understand that `callMcpTool()` is intercepted by the runtime
- ✅ **Local processing**: Keep intermediate data in execution environment with map/filter/reduce
- ✅ **State persistence**: Save full results to disk for later use
- ✅ **Context efficiency**: Return only summary (100 bytes) not full data (5KB+)
- ✅ **Real MCP calls**: See actual GitHub API responses via MCP protocol

## Next Steps

Try extending the script:
- Filter for files in specific directories
- Download and analyze file contents
- Build a reusable skill in `./skills/search-and-summarize.ts`

See: `docs/code-execution-with-mcp.md` for more patterns
