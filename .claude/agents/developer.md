---
model: sonnet
---

# Developer Agent

Instructions for writing Python scripts that interact with MCP servers.

## Progressive API Discovery

When working with MCP tools that have unknown response structures (marked with "no outputSchema"), ALWAYS use progressive discovery:

1. **First Script: Explore Raw Response**
   - Call the API with minimal parameters
   - Log the FULL raw response with `print(json.dumps(response, indent=2))` or `print(repr(response))`
   - Identify the actual structure

2. **Second Script: Extract Data**
   - Based on observed structure, write extraction logic
   - Use defensive coding patterns from README
   - Test with a small subset

3. **Final Script: Full Implementation**
   - Implement complete logic with proper error handling
   - Add user-friendly output formatting

## Example Workflow

**User Request:** "Analyze recent commits"

**Step 1 - Exploration:**
```python
# workspace/explore_git_log.py
import asyncio
import json
from runtime.mcp_client import call_mcp_tool

async def main():
    response = await call_mcp_tool("git__git_log", {"repo_path": ".", "max_count": 5})
    print('Raw response:', json.dumps(response, indent=2) if isinstance(response, dict) else repr(response))

asyncio.run(main())
```

**Step 2 - Extraction:**
```python
# Update after seeing the structure
async def main():
    response = await call_mcp_tool("git__git_log", {"repo_path": ".", "max_count": 5})
    
    # Defensive extraction
    if isinstance(response, str):
        lines = response.split('\n')
        print(f'Found {len(lines)} lines')
    elif isinstance(response, list):
        print(f'Found {len(response)} items')
    
    print('First item:', response[0] if response else None)

asyncio.run(main())
```

**Step 3 - Implementation:**
```python
# Now build the full feature with proper error handling and formatting
```

## Auto-Generated Wrapper Warnings

Wrappers without `outputSchema` use generic `Dict[str, Any]` return types. Always use defensive coding patterns when working with these tools.

Never assume response structure - always explore first!

## Defensive Coding Patterns

Since MCP response structures may vary, ALWAYS use defensive patterns:

### Handle Both Dict and Direct Responses

```python
# Try to get .value attribute, fall back to response itself
data = getattr(response, 'value', response)
```

### Ensure Lists Before Iteration

```python
items = response if isinstance(response, list) else []
for item in items:
    # safe to iterate
    pass
```

### Safe Property Access with Fallbacks

```python
# For dict-like objects
display_name = item.get('displayName', item.get('name', 'Unknown'))

# For objects with attributes
display_name = getattr(item, 'displayName', 'Unknown')
```

### Check for Nested Properties

```python
# API might return: { 'workItems': [...] } or just [...]
items = data.get('workItems', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
```

### Safe ID Extraction from References

```python
work_item_ids = [
    ref.get('target', {}).get('id') or ref.get('id')
    for ref in work_item_refs
]
# Filter out None values
work_item_ids = [id for id in work_item_ids if id is not None]
```

## Script Structure Template

All scripts in `workspace/` should follow this pattern:

```python
"""
Script description here.
"""

import asyncio
from runtime.mcp_client import call_mcp_tool

# Helper functions at top
def display_results(items: list, context: str) -> None:
    """Format and display results."""
    print(f"\n{context}:")
    for item in items:
        print(f"  - {item}")


async def main():
    """Main script logic."""
    try:
        # 1. Setup and parameters
        print('Starting task...')
        
        # 2. API calls with logging
        response = await call_mcp_tool("server__tool_name", {"param": "value"})
        print(f'Got response: {type(response).__name__}')
        
        # 3. Defensive data extraction
        data = getattr(response, 'value', response)
        items = data.get('items', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        
        # 4. Process and display
        display_results(items, 'Results')
        
        # 5. Return summary (not full data)
        return {
            "item_count": len(items),
            "processed": True
        }
        
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None


# Execute the script
# Note: The harness handles asyncio.run() for you, but for standalone scripts:
if __name__ == "__main__":
    result = asyncio.run(main())
    print(f'\nResult: {result}')
```

## Execution Methods

Scripts can be executed in two ways:

### Via Harness (Recommended)

```bash
uv run mcp-exec workspace/my_script.py
```

The harness automatically:
- Initializes MCP client manager
- Sets up Python path for imports
- Handles signals (SIGINT/SIGTERM)
- Cleans up connections on exit
- Manages asyncio event loop

### Standalone (For Testing)

```python
# Add asyncio.run() at the bottom
if __name__ == "__main__":
    result = asyncio.run(main())
```

Scripts executed this way need to handle their own cleanup, but can be useful for quick testing.

## When to Create Debug Scripts

Create a separate debug/exploration script when:

- Working with a new MCP tool for the first time
- Response structure is unclear or undocumented
- You encounter unexpected empty results
- The auto-generated wrapper returns `Dict[str, Any]` (no schema)

Name debug scripts: `workspace/debug_<feature>.py` or `workspace/explore_<api>.py`

## Field Normalization

### Server-Specific Normalization

Some MCP servers return fields with inconsistent casing. The runtime automatically normalizes these based on per-server strategies.

**Example: Azure DevOps (ADO)**

ADO APIs have inconsistent field casing:

- **Search API** returns `system.id`, `system.parent` (lowercase)
- **Work Item API** returns `System.Id`, `System.Parent` (PascalCase)

The runtime automatically normalizes ADO field prefixes to PascalCase:

```python
# Auto-normalization rules for ADO:
# system.* → System.*
# microsoft.* → Microsoft.*
# custom.* → Custom.*
# wef_* → WEF_*

work_item = await call_mcp_tool("ado__search_workitem", {...})
parent_id = work_item['fields']['System.Parent']  # ✓ Always works
# Don't use: work_item['fields']['system.parent']  # ✗ Won't work after normalization
```

**Impact:**

- Zero code changes needed when switching between different ADO APIs
- Consistent field access across all ADO tools
- No runtime errors from casing mismatches

### Adding Normalization for New Servers

If you encounter a new MCP server with inconsistent field names:

1. **Update `runtime/normalize_fields.py`:**

   ```python
   NORMALIZATION_CONFIG = NormalizationConfig(
       servers={
           "ado": "ado-pascal-case",
           "your-server": "your-strategy",  # Add new strategy
       }
   )
   ```

2. **Implement the strategy if needed:**

   ```python
   def normalize_your_server_fields(obj: Any) -> Any:
       """Your normalization logic."""
       # Your implementation
       pass
   ```

3. **Regenerate wrappers:**

   ```bash
   uv run mcp-generate
   ```

The generator automatically injects normalization into all wrappers for that server.

## Schema Discovery

### Type Safety for APIs Without Schemas

Many MCP servers don't provide `outputSchema` in their tool definitions because the underlying REST APIs lack formal schemas. This means auto-generated wrappers use generic `Dict[str, Any]` types.

**Schema discovery** lets you incrementally build Pydantic models from actual API responses.

### Setup

1. **Copy the example config:**

   ```bash
   cp discovery_config.example.json discovery_config.json
   ```

2. **Edit with your real data:**

   ```json
   {
     "servers": {
       "git": {
         "safeTools": {
           "git_status": {
             "description": "Get git status",
             "sampleParams": {
               "repo_path": "."
             }
           }
         }
       }
     }
   }
   ```

3. **Run discovery:**

   ```bash
   uv run mcp-discover
   ```

4. **Use the generated types:**

   ```python
   from servers.git import git_status
   from servers.git.discovered_types import GitStatusResult
   
   result = await git_status({"repo_path": "."})
   
   # If you need stronger typing (optional)
   if isinstance(result, dict) and 'value' in result:
       status_text = result['value']
   ```

### Safe vs Dangerous Tools

**Only configure read-only tools** in `safeTools`:

**✓ Safe (read-only):**

- `git_status` - reads git state
- `git_log` - reads commit history
- `fetch` - reads web content
- Any tool that just queries/fetches data

**✗ Dangerous (never add):**

- `git_commit` - modifies repository
- `git_push` - modifies remote
- Any tool that creates/modifies/deletes resources

Schema discovery will **call the tool with your sample parameters** to capture the response. Never use mutation operations!

### Important Caveats

1. **Fields are Optional** - All generated types mark fields as `Optional` because:
   - Responses vary by parameters
   - Different tool calls return different structures
   - Permissions affect what's returned

2. **Still use defensive coding** - Pydantic models are type hints, not runtime guarantees:

   ```python
   # Even with discovered types, still use defensive patterns
   title = work_item.get('fields', {}).get('System.Title', 'Untitled')
   tags = work_item.get('fields', {}).get('System.Tags', '').split(';') if work_item.get('fields', {}).get('System.Tags') else []
   ```

3. **Re-run when APIs change** - Discovered types can become stale as APIs evolve

4. **Types are hints, not guarantees** - Runtime shape can differ from the sample you discovered
