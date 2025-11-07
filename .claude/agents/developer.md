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
// tests/explore-backlog-api.ts
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

All scripts in `tests/` should follow this pattern:

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

Name debug scripts: `tests/debug-<feature>.ts` or `tests/explore-<api>.ts`
