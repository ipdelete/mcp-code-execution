# MCP Code Execution – Packaging Recommendation (Codex)

## Agreement With Claude's Recommendation
- I agree with Claude that a hybrid surface (library + CLI + MCP server) best matches how engineers and agents already touch this repo, and it solves the current discovery shortcomings in `servers/`.
- I diverge on rollout sequencing: we should ship a cleanly packaged library/CLI core first so the MCP server can layer on stable APIs instead of chasing churn during the refactor Claude proposes.
- I also recommend keeping the MCP tool surface intentionally small (wrapper generation, schema discovery, script execution) until we learn how agents actually orchestrate these tools; Claude's broader server plan risks unnecessary maintenance overhead.

## Key Architectural Observations
- `src/runtime/mcp_client.py` already encapsulates lazy server connections and is the natural boundary for both CLI commands and a future MCP server—no need to duplicate connection logic elsewhere.
- `src/runtime/harness.py` provides the lifecycle glue (asyncio, signals, cleanup) that every execution path reuses; packaging should keep it importable, not hide it behind CLI-only entry points.
- `src/runtime/generate_wrappers.py` and `src/runtime/discover_schemas.py` are pure functions over config + filesystem, which makes them safe to expose through multiple surfaces so long as we validate inputs.
- The CLI scripts (`mcp-generate`, `mcp-exec`, `mcp-discover`) are thin shims; consolidating them under a single Click/Typer CLI will reduce duplication and simplify docs.
- Progressive disclosure already depends on the `servers/` directory (gitignored) being regenerated; packaging should make that flow explicit so both engineers and agents know when they need a writable workspace.

## Packaging Recommendation (ranked)
1. **Hybrid, library-first** (primary): publish the `mcp_execution` library with clear APIs, ship a polished CLI (`mcp-exec`, `mcp-generate`, `mcp-discover`, `list-tools`), and layer a lightweight MCP server that invokes the same functions. This maximizes reuse and keeps agents from scraping the filesystem for discovery.
2. **Library-first only** (secondary): if timelines slip, releasing a clean library + CLI still improves adoption because engineers can `pip install mcp-execution` and agents can drive it through scripted harnesses.
3. **CLI-only** (fallback): keep the current install story but modernize the CLI UX. This is least desirable because it fails the “agents discover via MCP” requirement but can serve as a contingency plan if server work uncovers blockers.

## Architectural Changes Needed
- Rename the distributable package from the implicit `runtime` imports to an explicit `mcp_execution` module and re-export the stable surface in `src/runtime/__init__.py` for backward compatibility.
- Consolidate the CLI shims into a single command group (Click/Typer) that calls the same underlying functions used by the MCP server.
- Extract a shared “operations” layer (e.g., `src/runtime/operations.py`) that wraps `generate_wrappers`, `discover_schemas`, and the harness so both CLI and MCP server routes call identical code paths.
- Create a thin MCP server (`src/runtime/server.py`) that exposes three tools: `generate_wrappers`, `discover_schemas`, and `execute_script`, each validating params against existing Pydantic models.
- Update docs (README, AGENTS.md) to describe the three consumption modes and make `servers/` regeneration + workspace expectations explicit.

## Integration Plan
### Engineers
- Install via PyPI (`pip/uv pip install mcp-execution`) to gain direct imports such as `from mcp_execution import call_tool`.
- Use the consolidated CLI for day-to-day automation, optionally checking generated scripts into `workspace/`.
- Reference the shared operations layer inside CI/CD or IDE integrations without touching MCP server code.

### Agents
- Add the forthcoming `mcp-execution-server` entry point to their `mcp_config.json`; tools become discoverable through standard `/tools` calls instead of filesystem probing.
- Call `generate_wrappers` or `discover_schemas` with explicit config paths, then run scripts through `execute_script`, keeping large intermediate data local per the progressive disclosure model.
- Optionally import the same library inside sandboxed runtimes when direct MCP connections are unavailable (meaning the MCP server is optional, not mandatory).

## Implementation Priorities
1. **P0 – Packaging cleanup**: rename module, add explicit public API, ensure `pyproject.toml` metadata points to `mcp_execution`, and publish an initial PyPI release.
2. **P1 – CLI consolidation**: replace the three entry points with a single command group, add `--config`, `--workspace`, and `list-tools` helpers, and update documentation/tests.
3. **P2 – Shared operations layer**: refactor wrapper/schema/execution routines so they can be called synchronously or via asyncio without touching CLI code.
4. **P3 – MCP server**: build the MCP server process on top of the operations layer, add automated tests exercising each tool, and document the agent workflow.
5. **P4 – Observability & governance**: add structured logging around script execution, guardrails for long-running tasks, and optional telemetry hooks before advertising the server broadly.

## Risks & Open Questions
- Publishing a new package name may require a short-lived compatibility shim so downstream imports of `runtime.*` continue working.
- The MCP server will need rate limiting and sandbox knobs before it can be safely exposed to untrusted agents; we should scope these before GA.
- We should validate how often agents actually need schema discovery vs. wrapper generation to avoid over-investing in rarely used tools.
- Workspace write requirements (for `servers/` and `workspace/`) must be surfaced to hosted agent platforms so they provision persistent storage.
