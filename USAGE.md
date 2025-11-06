# Usage Guide

Complete guide to using the MCP Code Execution pattern.

## Table of Contents

- [Getting Started](#getting-started)
- [Writing Scripts](#writing-scripts)
- [Available MCP Servers](#available-mcp-servers)
- [Best Practices](#best-practices)
- [Advanced Usage](#advanced-usage)

## Getting Started

### 1. Installation

```bash
git clone https://github.com/yourusername/mcp-code-execution.git
cd mcp-code-execution
npm install
```

### 2. Verify Installation

List available MCP tools:

```bash
npm run exec workspace/test-list-tools.ts
```

You should see a list of available tools from configured servers.

### 3. Run Example

```bash
npm run exec workspace/example-data-processing.ts
```

## Writing Scripts

### Basic Script Template

Create `workspace/my-script.ts`:

```typescript
import { callMcpTool } from '../servers/mcp-client';

async function main() {
  try {
    // Call MCP tools
    const result = await callMcpTool('serverName__toolName', {
      param1: 'value1',
      param2: 'value2'
    });

    // Process data locally
    const processed = processData(result);

    // Return only summary
    console.log(JSON.stringify({ summary: processed }, null, 2));
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

main();
```

### Using TypeScript Wrappers

For cleaner code, use the provided wrappers:

```typescript
import * as github from '../servers/github-mcp';

async function main() {
  const results = await github.search_code({
    query: 'language:typescript repo:modelcontextprotocol/servers',
    perPage: 10
  });

  console.log(`Found ${results.items.length} files`);
}

main();
```

### Running Your Script

```bash
npm run exec workspace/my-script.ts
```

## Available MCP Servers

### Filesystem Server

**Configuration:**
```json
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"]
  }
}
```

**Available Tools:**
- `list_directory` - List files in a directory
- `read_file` - Read file contents
- `write_file` - Write to a file
- `create_directory` - Create a new directory
- And more...

**Example:**
```typescript
const listing = await callMcpTool('filesystem__list_directory', {
  path: '/allowed/path'
});
```

### GitHub Server

**Configuration:**
```json
{
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"]
  }
}
```

**Available Tools:**
- `search_code` - Search for code across GitHub
- `get_file_contents` - Get file/directory contents
- `create_pull_request` - Create a PR
- `create_issue` - Create an issue
- And 20+ more tools...

**Example:**
```typescript
import * as github from '../servers/github-mcp';

const results = await github.search_code({
  query: 'language:python',
  perPage: 10
});
```

## Best Practices

### 1. Keep Data Local

**❌ Bad:**
```typescript
// Don't pass large data through console.log
const files = await callMcpTool('filesystem__list_directory', { path: '/tmp' });
console.log(files); // 5KB to context!
```

**✅ Good:**
```typescript
// Process locally, return summary
const files = await callMcpTool('filesystem__list_directory', { path: '/tmp' });
const count = files.split('\n').length;
console.log({ fileCount: count }); // 50 bytes to context
```

### 2. Save Intermediate Results

```typescript
import * as fs from 'fs/promises';

// Fetch large data
const data = await callMcpTool('server__tool', params);

// Save to disk
await fs.writeFile('./workspace/data.json', JSON.stringify(data, null, 2));

// Process and return summary
const summary = createSummary(data);
console.log(summary);
```

### 3. Use TypeScript Types

```typescript
interface FileInfo {
  name: string;
  size: number;
  type: 'file' | 'directory';
}

const results = await callMcpTool<FileInfo[]>('filesystem__list', {
  path: '/tmp'
});
```

### 4. Handle Errors Gracefully

```typescript
try {
  const result = await callMcpTool('server__tool', params);
  // Process result
} catch (error) {
  console.error('MCP call failed:', error);
  // Fallback behavior
}
```

## Advanced Usage

### Parallel Calls

```typescript
// Fetch multiple resources in parallel
const [files, issues, pulls] = await Promise.all([
  callMcpTool('filesystem__list_directory', { path: '/tmp' }),
  github.list_issues({ owner: 'org', repo: 'repo' }),
  github.list_pull_requests({ owner: 'org', repo: 'repo' })
]);
```

### Complex Data Processing

```typescript
async function analyzeRepository(owner: string, repo: string) {
  // 1. Search for files
  const codeResults = await github.search_code({
    query: `repo:${owner}/${repo} language:typescript`
  });

  // 2. Fetch and analyze each file (stays local!)
  const analyses = await Promise.all(
    codeResults.items.slice(0, 10).map(async (item) => {
      const content = await github.get_file_contents({
        owner: item.repository.owner.login,
        repo: item.repository.name,
        path: item.path
      });

      return analyzeFile(content); // Process locally
    })
  );

  // 3. Save full results
  await fs.writeFile('./workspace/analysis.json', JSON.stringify(analyses, null, 2));

  // 4. Return only summary (to context)
  return {
    filesAnalyzed: analyses.length,
    averageComplexity: calculateAverage(analyses),
    topIssues: analyses.slice(0, 3).map(a => a.summary)
  };
}
```

### Building Reusable Skills

Create reusable functions in `workspace/skills/`:

```typescript
// workspace/skills/github-summary.ts
import * as github from '../../servers/github-mcp';

export async function getRepoSummary(owner: string, repo: string) {
  const [issues, pulls, commits] = await Promise.all([
    github.list_issues({ owner, repo }),
    github.list_pull_requests({ owner, repo }),
    github.list_commits({ owner, repo })
  ]);

  return {
    openIssues: issues.length,
    openPRs: pulls.length,
    recentCommits: commits.length
  };
}
```

Then use it:

```typescript
import { getRepoSummary } from './skills/github-summary';

const summary = await getRepoSummary('modelcontextprotocol', 'servers');
console.log(summary);
```

### Adding Custom MCP Servers

1. **Install the server:**
```bash
npm install -g @your-org/mcp-server-custom
```

2. **Add to config:**
```json
{
  "mcpServers": {
    "custom": {
      "command": "mcp-server-custom",
      "args": ["--port", "3000"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

3. **Create wrappers:**
```typescript
// servers/custom/index.ts
import { callMcpTool } from '../mcp-client';

export async function custom_tool(params: any) {
  return callMcpTool('custom__custom_tool', params);
}
```

4. **Use it:**
```typescript
import * as custom from '../servers/custom';

const result = await custom.custom_tool({ param: 'value' });
```

## Debugging

### Enable Debug Logging

Set environment variable before running:

```bash
DEBUG=mcp:* npm run exec workspace/my-script.ts
```

### List Available Tools

```bash
npm run exec workspace/test-list-tools.ts
```

### Test Server Connection

```typescript
import { getMcpClientManager } from '../runtime/mcp-client-impl';

async function main() {
  const manager = getMcpClientManager();
  await manager.initialize();

  const tools = await manager.listAllTools();
  console.log(`Connected to ${tools.length} tools`);

  await manager.cleanup();
}

main();
```

## Common Patterns

### Pattern: Filter Large Dataset

```typescript
// Fetch large dataset (stays local)
const allData = await callMcpTool('server__get_data', { limit: 10000 });

// Filter locally
const filtered = allData.filter(item => item.status === 'active');

// Return summary
console.log({ total: allData.length, active: filtered.length });
```

### Pattern: Aggregate Multiple Sources

```typescript
const sources = ['source1', 'source2', 'source3'];

const data = await Promise.all(
  sources.map(source => callMcpTool('server__fetch', { source }))
);

const aggregated = aggregateData(data); // Process locally
console.log(createSummary(aggregated)); // Return summary
```

### Pattern: Incremental Processing

```typescript
const items = await callMcpTool('server__list_items', {});

for (const item of items) {
  await processItem(item); // Process each locally
  await saveProgress(item.id); // Save state
}

console.log({ processed: items.length }); // Return summary
```

## Next Steps

- Read the [Architecture Guide](./README.md#architecture)
- Check [Example Scripts](./workspace/)
- Review [Anthropic's Article](https://www.anthropic.com/engineering/code-execution-with-mcp)
- Explore [MCP Servers](https://github.com/modelcontextprotocol/servers)
