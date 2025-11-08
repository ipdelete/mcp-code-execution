# MCP Code Execution – Copilot's Packaging Recommendation

## Agreement Analysis

### Alignment with Claude Code (CC)
**Agree:**
- Hybrid approach (library + CLI + MCP server) is architecturally sound
- Discovery via filesystem is fragile; agents need native MCP protocol
- Current package naming (`runtime.*` imports vs `mcp-execution` package) is confusing
- Progressive disclosure pattern (98.7% token reduction) is the core innovation to preserve

**Disagree:**
- CC's 4-phase rollout (4 weeks) is over-engineered for a 1,810 LOC codebase
- Full package rename (`runtime` → `mcp_execution`) creates unnecessary migration churn
- MCP server should be minimal initially, not feature-complete as CC proposes

### Alignment with Codex (CX)
**Agree:**
- Library-first sequencing prevents the MCP server from building on unstable APIs
- Operations layer is the right abstraction for code reuse across surfaces
- Keep MCP tool surface intentionally small until usage patterns emerge
- Workspace/filesystem expectations must be explicit in docs

**Disagree:**
- CX's P0-P4 priorities are too conservative; we can ship hybrid in parallel, not serial phases
- Observability/governance (P4) is premature optimization before user adoption
- Compatibility shims for `runtime.*` imports add complexity with no clear user base

## Core Architectural Insight

Both CC and CX missed a critical point: **this project is already hybrid**.

Looking at `pyproject.toml`:
- Package name: `mcp-execution` ✅
- Entry points: `mcp-exec`, `mcp-generate`, `mcp-discover` ✅
- Library imports: `runtime.*` (works via `[tool.pytest] pythonpath = ["src"]`) ✅

The architecture doesn't need refactoring—it needs **clarification and one missing piece** (the MCP server).

## Recommendation: Pragmatic Hybrid (Ship in 2 Days)

### 1. Keep Current Architecture
**No renaming.** Current state analysis:
- `src/runtime/` is already the package root
- Import path `from runtime.mcp_client import ...` works fine
- Entry points in `pyproject.toml` reference `runtime.module:main`
- Tests import `from runtime.*` successfully

The confusion is *documentation*, not code. Fix AGENTS.md and README, not imports.

### 2. Add MCP Server (Minimal)
Create `src/runtime/server.py` (~150 LOC) exposing exactly 3 tools:

```python
@mcp.tool()
async def generate_wrappers(config_path: str = "mcp_config.json") -> dict:
    """Generate typed Python wrappers from MCP server configs."""
    # Call existing generate_wrappers.generate_all_wrappers()
    
@mcp.tool()
async def discover_schemas(
    config_path: str = "mcp_config.json",
    discovery_config: str = "discovery_config.json"
) -> dict:
    """Discover Pydantic types from actual API responses."""
    # Call existing discover_schemas.discover_all_schemas()

@mcp.tool()
async def execute_script(
    script_path: str,
    timeout: int = 300
) -> dict:
    """Execute Python script with MCP harness."""
    # Call existing harness.run_script()
```

Add entry point to `pyproject.toml`:
```toml
[project.scripts]
mcp-execution-server = "runtime.server:main"
```

**Why minimal?** CC proposed 5 tools (`list_available_tools`, `get_tool_schema`, etc.). Those are premature—agents already have filesystem access to `servers/` post-generation. Ship the core loop first.

### 3. Documentation Over Abstraction
CX wants an "operations layer" to deduplicate CLI/server code. **Not needed.** Current functions in `generate_wrappers.py` and `discover_schemas.py` are already pure—both CLI and MCP server can import them directly:

```python
# CLI (current)
from runtime.generate_wrappers import generate_all_wrappers
generate_all_wrappers(config_path)

# MCP server (new)
from runtime.generate_wrappers import generate_all_wrappers
result = await asyncio.to_thread(generate_all_wrappers, config_path)
```

No abstraction layer needed. If duplication emerges later, refactor then.

### 4. Fix Documentation (Critical)
Both CC and CX noted the discovery problem but didn't emphasize *why*. Current `AGENTS.md` says:

> "Progressive disclosure: list `servers/` → read needed tools → lazy connect"

This teaches agents the **wrong pattern**. Update to:

> **For Agents**: Add `mcp-execution-server` to your MCP config. Call `generate_wrappers()` to create typed wrappers, then import from `servers/` in your scripts. Never read `servers/` before generation—it's gitignored and won't exist.

> **For Engineers**: `pip install mcp-execution`, run `mcp-generate`, import from `runtime.*` or use generated `servers/` wrappers.

## Implementation Plan (2 Days, Not 4 Weeks)

### Day 1: MCP Server
- [ ] Create `src/runtime/server.py` with 3 tools (2 hours)
- [ ] Add `mcp-execution-server` entry point (5 minutes)
- [ ] Test with Claude Desktop config (1 hour)
- [ ] Add integration test in `tests/integration/test_mcp_server.py` (1 hour)

### Day 2: Documentation
- [ ] Update README with three usage modes: Library, CLI, MCP Server (1 hour)
- [ ] Rewrite AGENTS.md to show MCP-first workflow (30 minutes)
- [ ] Add `examples/agent_workflow.md` showing actual Claude conversation (30 minutes)
- [ ] Publish to PyPI with current version (30 minutes)

Total: ~6 hours focused work.

## Why This Beats CC and CX

**vs Claude Code's 4-week plan:**
- CC wants to rename `runtime` → `mcp_execution` (P1). Why? Current imports work fine.
- CC plans a "library API facade" (P1). We already have one—it's `src/runtime/*.py`.
- CC schedules MCP server for Week 2. We can ship it Day 1 because the functions already exist.

**vs Codex's P0-P4 priorities:**
- CX gates MCP server (P3) behind "shared operations layer" (P2). That's over-abstraction.
- CX wants "observability & governance" (P4) before promoting the server. Premature—ship, learn, iterate.
- CX recommends compatibility shims for `runtime.*` imports. No one is using this in prod yet (v2.0.0 just released per `pyproject.toml`).

## Integration Points

### Engineers (Unchanged)
```bash
pip install mcp-execution
mcp-generate  # CLI
# or
from runtime.mcp_client import get_mcp_client_manager  # Library
```

### Agents (New)
**claude_desktop_config.json:**
```json
{
  "mcpServers": {
    "code-execution": {
      "command": "mcp-execution-server"
    }
  }
}
```

**Agent workflow:**
1. Discover tool `generate_wrappers` via MCP `/tools`
2. Call `generate_wrappers()` → creates `servers/` directory
3. Write Python script importing from `servers.git`, `servers.fetch`
4. Call `execute_script(script_path="workspace/analyze.py")`
5. Get summary output (not full data dump)

## Risks & Mitigations

**Risk 1: MCP server bugs block agent usage**
- Mitigation: CLI remains independent. Engineers unaffected.

**Risk 2: Server performance issues with large schemas**
- Mitigation: Generation happens once per config change, not per-tool-call.

**Risk 3: Workspace write permissions in hosted environments**
- Mitigation: Document in README that `servers/` and `workspace/` need write access. This is already true for CLI usage.

## Decision Matrix

| Approach | Ship Time | Agent Discovery | Eng UX | Maintenance |
|----------|-----------|----------------|---------|-------------|
| CC (4-phase) | 4 weeks | ✅ Native MCP | ⚠️ Breaking rename | ⚠️ High (multi-package) |
| CX (P0-P4) | 3 weeks | ✅ Native MCP | ✅ Stable | ⚠️ Medium (abstraction) |
| **CO (Pragmatic)** | **2 days** | **✅ Native MCP** | **✅ Stable** | **✅ Low (additive)** |

## What's Actually Blocking Adoption?

Not architecture. Not packaging. **Discoverability.**

1. Not on MCP server registry → agents don't know it exists
2. AGENTS.md teaches filesystem scraping → agents do the wrong thing
3. No agent usage examples → Claude doesn't see the pattern

The MCP server fixes #1 and #2. Day 2 docs fix #3.

## Conclusion

**Primary recommendation**: Add minimal MCP server (`runtime/server.py`, 3 tools) and rewrite agent documentation. Ship in 2 days.

**Why pragmatic hybrid wins:**
- Preserves all current functionality (library, CLI)
- Adds agent discoverability via standard MCP protocol
- Zero breaking changes for engineers
- Ships 14x faster than CC's plan, 10x faster than CX's plan
- Learns from real usage before investing in abstractions

The codebase is already clean (1,810 LOC, type-safe, tested). Both CC and CX over-engineered because they assumed a larger refactor was needed. It's not. The progressive disclosure pattern works. We just need agents to discover it through MCP, not filesystem hacks.

**Next steps:**
1. Create `src/runtime/server.py` (copy pattern from MCP SDK examples)
2. Test with Claude Desktop
3. Update AGENTS.md with MCP-first workflow
4. Ship v2.1.0 to PyPI

The architecture is sound. The code is ready. Let's ship it.
