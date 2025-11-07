---
description: Phase 0 - Proof of Concept (CRITICAL BLOCKER)
model: sonnet
---

# Phase 0: Proof of Concept - Python MCP SDK Validation

**Goal**: Validate Python MCP SDK compatibility before committing to architecture

**Tasks**: T001-T011 | **Validation**: CHK011-CHK015

## Context

This is a CRITICAL BLOCKER phase. We must validate that the Python MCP SDK supports:
- stdio transport with subprocess MCP servers
- Connection lifecycle (connect → initialize → call → close)
- Response structure matching TypeScript expectations
- Defensive unwrapping patterns

**GO/NO-GO DECISION**: Only proceed to Phase 1 if PoC succeeds.

## Instructions

Execute the following tasks in order:

### 1. Setup Test Environment (T001)

```bash
# Install Python MCP SDK in temporary environment
uv pip install mcp
```

### 2. Create PoC Script (T002-T007)

Create `poc_mcp_test.py` that validates:
- ✅ stdio transport connection to git server
- ✅ Client initialization and list_tools() format
- ✅ Tool calling with git_status
- ✅ Response unwrapping pattern (.content attribute)
- ✅ Connection lifecycle

Use this template:

```python
"""
PoC: Validate Python MCP SDK compatibility
Tests stdio transport, connection lifecycle, and response structure
"""
import asyncio
from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_mcp_connection():
    """Test connecting to git MCP server"""
    print("🧪 Testing Python MCP SDK with git server...")

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-git"]
    )

    async with stdio_client(server_params) as (read, write):
        async with Client(read, write) as client:
            # Test 1: Initialize
            print("\n✓ Test 1: Initialize connection")
            await client.initialize()

            # Test 2: List tools
            print("✓ Test 2: List tools")
            tools = await client.list_tools()
            print(f"  Found {len(tools.tools)} tools")
            for tool in tools.tools:
                print(f"    - {tool.name}: {tool.description}")

            # Test 3: Call tool
            print("\n✓ Test 3: Call git_status tool")
            result = await client.call_tool(
                name="git_status",
                arguments={"repo_path": "."}
            )

            # Test 4: Validate response structure
            print("\n✓ Test 4: Validate response structure")
            print(f"  Result type: {type(result)}")
            print(f"  Result attributes: {dir(result)}")

            # Test defensive unwrapping
            if hasattr(result, 'content'):
                print("  ✅ Has .content attribute")
                if isinstance(result.content, list):
                    print(f"  ✅ Content is list with {len(result.content)} items")
                    if result.content:
                        print(f"  ✅ First item type: {type(result.content[0])}")

            print("\n✅ Git server validation complete")
            return True

if __name__ == "__main__":
    success = asyncio.run(test_mcp_connection())
    print(f"\n{'✅ PoC PASSED' if success else '❌ PoC FAILED'}")
```

### 3. Test with Git Server (T003-T007)

```bash
python poc_mcp_test.py
```

Verify output shows:
- ✅ Connection succeeds
- ✅ Tools listed (git_status, git_log, git_diff, etc.)
- ✅ Tool call succeeds
- ✅ Response has expected structure

### 4. Test with Fetch Server (T008)

Create `poc_mcp_fetch_test.py` for fetch server validation:

```python
"""PoC: Validate Python MCP SDK with fetch server"""
import asyncio
from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_fetch_server():
    """Test connecting to fetch MCP server"""
    print("🧪 Testing Python MCP SDK with fetch server...")

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-fetch"]
    )

    async with stdio_client(server_params) as (read, write):
        async with Client(read, write) as client:
            await client.initialize()

            # List tools
            tools = await client.list_tools()
            print(f"✓ Found {len(tools.tools)} tools")
            for tool in tools.tools:
                print(f"  - {tool.name}")

            # Test fetch tool
            result = await client.call_tool(
                name="fetch",
                arguments={"url": "https://example.com"}
            )

            print(f"✓ Result type: {type(result)}")
            print(f"✓ Has content: {hasattr(result, 'content')}")

            print("\n✅ Fetch server validation complete")
            return True

if __name__ == "__main__":
    success = asyncio.run(test_fetch_server())
    print(f"\n{'✅ PoC PASSED' if success else '❌ PoC FAILED'}")
```

```bash
python poc_mcp_fetch_test.py
```

### 5. Document Findings (T009-T010)

Create `poc_findings.md` documenting:
- SDK version tested
- Response structure details
- Any differences from TypeScript SDK
- Defensive unwrapping patterns observed
- Recommendations for implementation

### 6. GO/NO-GO Decision (T011)

Review findings and make decision:
- ✅ **GO**: SDK is compatible, proceed to Phase 1
- ❌ **NO-GO**: SDK has blocking issues, revise architecture

Document decision in `poc_findings.md`

## Validation Checklist

Run through these checks:

- [ ] CHK011 - PoC validates all critical assumptions (stdio transport, SDK compatibility, response structure)?
- [ ] CHK012 - Both test servers (git, fetch) tested?
- [ ] CHK013 - PoC script executable standalone?
- [ ] CHK014 - PoC deliverables measurable (✅ checklist)?
- [ ] CHK015 - Contingency plan if SDK incompatible?

## Deliverables

- ✅ `poc_mcp_test.py` (working git server test)
- ✅ `poc_mcp_fetch_test.py` (working fetch server test)
- ✅ `poc_findings.md` (documentation of findings)
- ✅ GO/NO-GO decision documented

## Success Criteria

Only proceed to Phase 1 if:
1. Both servers connect successfully
2. Tools can be listed and called
3. Response structure is predictable
4. Defensive unwrapping pattern is clear

## Mark Items Complete

After successfully completing this phase, mark the following as complete:

### Update CHECKLIST.md (CHK011-CHK015)
```bash
# Mark checklist items complete
sed -i '' 's/^- \[ \] CHK011/- [x] CHK011/' CHECKLIST.md
sed -i '' 's/^- \[ \] CHK012/- [x] CHK012/' CHECKLIST.md
sed -i '' 's/^- \[ \] CHK013/- [x] CHK013/' CHECKLIST.md
sed -i '' 's/^- \[ \] CHK014/- [x] CHK014/' CHECKLIST.md
sed -i '' 's/^- \[ \] CHK015/- [x] CHK015/' CHECKLIST.md

echo "✅ Phase 0 checklist items marked complete"
```

### Update TASKS.md (T001-T011)
```bash
# Mark task items complete
sed -i '' 's/^- \[ \] T001/- [x] T001/' TASKS.md
sed -i '' 's/^- \[ \] T002/- [x] T002/' TASKS.md
sed -i '' 's/^- \[ \] T003/- [x] T003/' TASKS.md
sed -i '' 's/^- \[ \] T004/- [x] T004/' TASKS.md
sed -i '' 's/^- \[ \] T005/- [x] T005/' TASKS.md
sed -i '' 's/^- \[ \] T006/- [x] T006/' TASKS.md
sed -i '' 's/^- \[ \] T007/- [x] T007/' TASKS.md
sed -i '' 's/^- \[ \] T008/- [x] T008/' TASKS.md
sed -i '' 's/^- \[ \] T009/- [x] T009/' TASKS.md
sed -i '' 's/^- \[ \] T010/- [x] T010/' TASKS.md
sed -i '' 's/^- \[ \] T011/- [x] T011/' TASKS.md

echo "✅ Phase 0 task items marked complete"
```

### Verify Completion
```bash
# Verify all Phase 0 items marked
grep "CHK01[1-5]" CHECKLIST.md | grep "\[x\]" | wc -l  # Should be 5
grep "T00[1-9]\|T01[01]" TASKS.md | grep "\[x\]" | wc -l  # Should be 11

echo "✅ Phase 0 complete and documented"
```

---

**Next Phase**: If GO decision, proceed to `/phase1-setup`
