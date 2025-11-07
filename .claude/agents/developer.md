---
model: sonnet
---

# Developer Agent

Instructions for writing scripts that interact with MCP servers.

## Progressive API Discovery

When working with MCP tools that have unknown response structures (marked with "no outputSchema"), ALWAYS use progressive discovery:

1. **First Script: Explore Raw Response**
   - Call the API with minimal parameters
   - Log the FULL raw response with `console.log(JSON.stringify(response, null, 2))`
   - Identify the actual structure

2. **Second Script: Extract Data**
   - Based on observed structure, write extraction logic
   - Use defensive coding patterns from README
   - Test with a small subset

3. **Final Script: Full Implementation**
   - Implement complete logic with proper error handling
   - Add user-friendly output formatting

## Example Workflow

**User Request:** "List features for team X"

**Step 1 - Exploration:**
```typescript
// workspace/explore-backlog-api.ts
const response = await wit_list_backlog_work_items({...});
console.log('Raw response:', JSON.stringify(response, null, 2));
```

**Step 2 - Extraction:**
```typescript
// Update after seeing: { workItems: [...] }
const data = response.value || response;
const items = data.workItems || [];
console.log(`Found ${items.length} items`);
console.log('First item:', JSON.stringify(items[0], null, 2));
```

**Step 3 - Implementation:**
```typescript
// Now build the full feature with proper typing and formatting
```

## Auto-Generated Wrapper Warnings

All wrappers with this warning need progressive discovery:
```
⚠ No outputSchema for <tool_name> - using generic type
```

Never assume response structure - always explore first!

## Defensive Coding Patterns

Since MCP response structures may vary, ALWAYS use defensive patterns:

### Handle Both Wrapped and Direct Responses
```typescript
const data = response.value || response;
```

### Ensure Arrays Before Using Array Methods
```typescript
const items = Array.isArray(data) ? data : [];
items.forEach(item => { /* safe */ });
```

### Safe Property Access with Fallbacks
```typescript
const displayName = field?.displayName || field || 'Unknown';
```

### Check for Nested Properties
```typescript
// API might return: { workItems: [...] } or just [...]
const items = data.workItems || (Array.isArray(data) ? data : []);
```

### Safe ID Extraction from References
```typescript
const workItemIds = workItemRefs
  .map((ref: any) => ref.target?.id || ref.id)
  .filter((id: any) => id !== undefined);
```

## Script Structure Template

All scripts in `workspace/` should follow this pattern:

```typescript
import { tool1, tool2 } from '../servers/server-name';

// Helper functions at top
function displayResults(items: any[], context: string) {
  // Formatting logic
}

async function main() {
  try {
    // 1. Setup and parameters
    console.log('Starting task...');
    
    // 2. API calls with logging
    const response = await tool1({ params });
    console.log(`Got ${response.length} results`);
    
    // 3. Defensive data extraction
    const data = response.value || response;
    const items = data.items || (Array.isArray(data) ? data : []);
    
    // 4. Process and display
    displayResults(items, 'context');
    
  } catch (error: any) {
    console.error('Error:', error.message || error);
    if (error.stack) {
      console.error('\nStack trace:', error.stack);
    }
    process.exit(1);
  }
}

main().then(() => {
  process.exit(0);
}).catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
```

## Process Exit Handling

**ALWAYS include proper exit codes** to ensure scripts terminate cleanly:

- Success: `process.exit(0)`
- Failure: `process.exit(1)`
- Always wrap in `.then()/.catch()` handlers

## When to Create Debug Scripts

Create a separate debug/exploration script when:
- Working with a new MCP tool for the first time
- Response structure is unclear or undocumented
- You encounter unexpected empty results
- The auto-generated wrapper shows "no outputSchema" warning

Name debug scripts: `workspace/debug-<feature>.ts` or `workspace/explore-<api>.ts`

## Field Normalization

### Azure DevOps Auto-Normalization

**All ADO tool responses are automatically normalized to PascalCase** for consistent field access.

Azure DevOps APIs have inconsistent field casing:
- **Search API** returns `system.id`, `system.parent` (lowercase)
- **Work Item API** returns `System.Id`, `System.Parent` (PascalCase)

The `ado` MCP server automatically normalizes ALL field names to PascalCase before returning them to your code. This means:

**You can always use PascalCase:**
```typescript
// Works for ALL ADO tools - search, get, batch, etc.
const workItem = await search_workitem({...});
const parentId = workItem.fields['System.Parent']; // ✓ Always works

// Don't do this:
const parentId = workItem.fields['system.parent']; // ✗ Won't work after normalization
```

**Impact:**
- Zero code changes needed when switching between different ADO APIs
- Consistent field access across all 77 ADO tools
- No runtime errors from casing mismatches

This normalization is transparent and automatic. No configuration needed.

## Schema Discovery

### Type Safety for APIs Without Schemas

Many MCP servers (like Azure DevOps) don't provide `outputSchema` in their tool definitions because the underlying REST APIs lack formal OpenAPI/JSON schemas. This means auto-generated wrappers use generic `any` types.

**Schema discovery** lets you incrementally build TypeScript interfaces from actual API responses.

### Setup

1. **Copy the example config:**
   ```bash
   cp discovery-config.example.json discovery-config.json
   ```

2. **Edit with your real data:**
   ```json
   {
     "servers": {
       "ado": {
         "safeTools": {
           "wit_get_work_item": {
             "description": "Get work item details",
             "sampleParams": {
               "id": 2421643,  // Your real work item ID
               "project": "Your Project Name",
               "expand": "relations"
             }
           }
         }
       }
     }
   }
   ```

3. **Run discovery:**
   ```bash
   npm run discover-schemas
   ```

4. **Use the generated types:**
   ```typescript
   import { wit_get_work_item } from '../servers/ado';
   import type { WitGetWorkItemResult } from '../servers/ado/discovered-types';
   
   const workItem = await wit_get_work_item({ id: 123, project: 'MyProject' }) as WitGetWorkItemResult;
   
   // Now have IntelliSense for the structure
   const title = workItem.fields?.['System.Title'];
   const parent = workItem.fields?.['System.Parent'];
   ```

### Safe vs Dangerous Tools

**Only configure read-only tools** in `safeTools`:

**✓ Safe (read-only):**
- `wit_get_work_item`
- `search_workitem`
- `core_list_projects`
- `repo_list_repos_by_project`
- Any tool that just queries/fetches data

**✗ Dangerous (never add):**
- `wit_create_work_item` - creates data
- `wit_update_work_item` - modifies data
- `repo_create_pull_request` - creates resources
- `pipelines_run_pipeline` - triggers builds

Schema discovery will **call the tool with your sample parameters** to capture the response. Never use mutation operations!

### Important Caveats

1. **Fields are optional** - All generated types mark fields as `?` because:
   - Responses vary by parameters (e.g., `expand='none'` vs `expand='relations'`)
   - Work item types have different fields (Feature vs Task vs Bug)
   - Permissions affect what's returned
   
2. **Still use defensive coding** - TypeScript types are compile-time hints only:
   ```typescript
   // Even with discovered types, still use defensive patterns
   const title = workItem.fields?.['System.Title'] || 'Untitled';
   const tags = workItem.fields?.['System.Tags']?.split(';') || [];
   ```

3. **Re-run when APIs change** - Discovered types can become stale as APIs evolve

4. **Types are hints, not guarantees** - Runtime shape can differ from the sample you discovered

### Adding Normalization for New Servers

If you encounter a new MCP server with inconsistent field names:

1. **Add normalization strategy to `runtime/normalize-fields.ts`:**
   ```typescript
   export const NORMALIZATION_CONFIG: Record<string, NormalizationStrategy> = {
     ado: {
       enabled: true,
       strategy: 'pascalcase-dotted'
     },
     'your-server': {
       enabled: true,
       strategy: 'custom-strategy-name'
     }
   };
   ```

2. **Implement the strategy if needed:**
   ```typescript
   function normalizeYourServer(obj: any): any {
     // Your normalization logic
   }
   ```

3. **Regenerate wrappers:**
   ```bash
   npm run generate
   ```

The generator will automatically inject normalization into all wrappers for that server.
