# MCP Server Tool Wrappers

TypeScript modules that wrap MCP server tools for use in code execution environments, implementing the pattern from [Code Execution with MCP](../docs/code-execution-with-mcp.md).

## Architecture

```
servers/
├── mcp-client.ts           # Core MCP protocol client
├── github-mcp/             # GitHub MCP server
│   ├── index.ts            # Public API exports
│   ├── search_code.ts      # Code search tool
│   └── get_file_contents.ts # File/directory access
└── [other-servers]/        # Additional MCP servers
```

## How It Works

Each MCP server is wrapped as a TypeScript module. Instead of:

```typescript
// Traditional: Tool definition in context, direct call
TOOL CALL: github-search_code({ query: "..." })
→ Results flow through model context
```

You import and use as code:

```typescript
// Code execution: Import as module
import * as github from './servers/github-mcp';

const results = await github.search_code({ query: "..." });
// Results stay in execution environment
```

## Benefits

1. **Progressive Tool Loading** - Import only needed tools, not entire server definitions
2. **Efficient Data Flow** - Intermediate results never touch model context
3. **Type Safety** - Full TypeScript IntelliSense and compile-time checking
4. **Standard Composition** - Use async/await, Promise.all, loops, etc.

## Usage

### Search Code

```typescript
import * as github from './servers/github-mcp';

// Search for Python code in an organization
const results = await github.search_code({
  query: 'content:Skill language:Python org:github',
  perPage: 10
});

// Process results without passing through model context
const matches = results.items.map(item => ({
  file: item.path,
  repo: item.repository.full_name
}));

console.log(`Found ${matches.length} matches`);
```

### Get File Contents

```typescript
import * as github from './servers/github-mcp';

// Get a specific file
const readme = await github.get_file_contents({
  owner: 'github',
  repo: 'github-mcp-server',
  path: 'README.md'
});

// If it's a file, decode the content
if ('content' in readme && readme.encoding === 'base64') {
  const content = Buffer.from(readme.content, 'base64').toString('utf-8');
  console.log(content);
}

// List directory contents
const srcFiles = await github.get_file_contents({
  owner: 'github',
  repo: 'github-mcp-server',
  path: 'src/'
});

console.log(`Found ${srcFiles.length} files in src/`);
```

### Composing Multiple Operations

The key advantage is composing operations efficiently:

```typescript
import * as github from './servers/github-mcp';

// Search for all README files in a repo
const readmes = await github.search_code({
  query: 'repo:github/github-mcp-server filename:README'
});

// Fetch each one and process - data stays in execution environment
const contents = await Promise.all(
  readmes.items.slice(0, 5).map(async (item) => {
    const file = await github.get_file_contents({
      owner: item.repository.owner.login,
      repo: item.repository.name,
      path: item.path
    });
    
    if ('content' in file) {
      return {
        path: item.path,
        size: file.size,
        // Process without sending full content to model
        hasInstallSection: Buffer.from(file.content, 'base64')
          .toString('utf-8')
          .includes('## Install')
      };
    }
  })
);

// Only summary goes back to model, not full file contents
console.log(`Analyzed ${contents.length} READMEs`);
console.log(`${contents.filter(c => c?.hasInstallSection).length} have install sections`);
```

## Adding New MCP Servers

To wrap a new MCP server:

1. Create a directory: `servers/my-server/`
2. For each tool, create `toolName.ts`:
   ```typescript
   import { callTool } from '../mcp-client';
   
   export async function myTool(params: MyParams) {
     return callTool('my-server', 'myTool', params);
   }
   ```
3. Export from `index.ts`:
   ```typescript
   export * from './myTool';
   ```

## Implementation Status

- **mcp-client.ts** - Core protocol client (currently uses GitHub Copilot's native MCP integration)
- **github-mcp/** - GitHub server wrapper (functional)
- **Other servers** - Add as needed

## Privacy & Security

This pattern enables:

- **Privacy-preserving operations** - Intermediate data stays local
- **Tokenization** - MCP client can tokenize PII before model sees it
- **Deterministic security** - Define explicit rules for data flow

Example with PII tokenization:
```typescript
const sheet = await gdrive.getSheet({ id: 'abc123' });
// MCP client tokenizes: [EMAIL_1], [PHONE_1], etc.

await salesforce.updateRecord({
  data: { Email: sheet.rows[0].email } 
  // MCP client untokenizes on send
});
// Real emails flow between systems, model never sees them
```

## Further Reading

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Code Execution Article](../docs/code-execution-with-mcp.md)
- [Official MCP Servers](https://github.com/modelcontextprotocol/servers)
