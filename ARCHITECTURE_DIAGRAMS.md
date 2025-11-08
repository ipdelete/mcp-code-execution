# Architecture Diagrams: Output Schema Solution

## Diagram 1: Current State - Scattered Type Knowledge

```
┌─────────────────────────────────────────────────────────────┐
│                     Current Architecture                     │
└─────────────────────────────────────────────────────────────┘

    MCP Server (outputSchema=None)
           │
           ▼
    ┌──────────────────────────┐
    │  generate_wrappers.py    │
    │  ─────────────────────   │
    │  Decision: Declared?     │
    │  ├─ Yes → Pydantic       │
    │  └─ No → Dict[str, Any]  │
    └──────────────────────────┘
           │
           ▼
    ┌──────────────────────────┐
    │  Generated Wrapper       │
    │  ─────────────────────   │
    │  async def tool()        │
    │    → Dict[str, Any]      │  ◄── STATIC: Never improves
    └──────────────────────────┘
           │
           ▼
    ┌──────────────────────────┐
    │  Agent Script            │
    │  ─────────────────────   │
    │  result = await tool()   │
    │  if isinstance(result):  │
    │    if "field" in result: │
    │      value = result[...] │  ◄── 150 tokens of defensive code
    │      ...                 │
    └──────────────────────────┘

Separate (Manual) Process:

    ┌──────────────────────────┐
    │  discover_schemas.py     │  ◄── Must run manually
    │  ─────────────────────   │
    │  Execute safe tools      │
    │  Infer types            │
    │  Write to .py file      │  ◄── Not integrated with wrappers
    └──────────────────────────┘

Problems:
  ✗ No coordination between discovery and generation
  ✗ Types never improve after initial generation
  ✗ No metrics on schema quality
  ✗ Discovery is opt-in, separate step
```

---

## Diagram 2: Proposed State - Unified Learning Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Proposed Architecture                      │
└─────────────────────────────────────────────────────────────┘

                    MCP Server (outputSchema=None)
                           │
                           ▼
                    ┌─────────────────┐
                    │ Type Registry   │ ◄── CENTRAL SOURCE OF TRUTH
                    │ ────────────── │
                    │ • Tool schemas  │
                    │ • Observations  │
                    │ • Quality       │
                    │ • Inferred      │
                    └─────────────────┘
                      ▲           ▲
                      │           │
          ┌───────────┘           └──────────────┐
          │                                      │
          │                                      │
    ┌─────┴──────────┐                  ┌────────┴─────────┐
    │ generate_      │                  │ mcp_client.py    │
    │   wrappers.py  │                  │ ────────────────│
    │ ────────────── │                  │ After each exec: │
    │ 1. Register    │                  │ observe_         │
    │ 2. Check       │                  │   execution()    │
    │    quality     │                  │                  │
    │ 3. Generate    │                  │ Updates:         │
    │    adaptive    │                  │ • Obs count      │
    │    wrapper     │                  │ • Field types    │
    └────────────────┘                  │ • Consistency    │
          │                             └──────────────────┘
          ▼                                      │
                                                 │
    ┌─────────────────────────┐                 │
    │ Schema Evolution Mgr    │ ◄───────────────┘
    │ ─────────────────────── │
    │ Background Task:        │
    │ • Check quality         │
    │ • Detect improvements   │
    │ • Regenerate wrappers   │
    └─────────────────────────┘
          │
          ▼

┌──────────────────────────────────────────────────────────────┐
│                  Generated Wrappers (Adaptive)                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Day 1: Unknown Schema                                       │
│  ──────────────────────                                      │
│  async def tool(params) → ToolResponse:                      │
│    """Schema: UNKNOWN (will improve)"""                      │
│    # Returns helper wrapper with safe accessors              │
│                                                              │
│  ┌────────────────────────────────────────────┐             │
│  │ After 10+ consistent observations          │             │
│  │ Evolution Manager detects improvement      │             │
│  │ Wrapper auto-regenerates ↓                 │             │
│  └────────────────────────────────────────────┘             │
│                                                              │
│  Day 7: Inferred Schema (Low Quality)                        │
│  ─────────────────────────────────                           │
│  async def tool(params) → ToolResult:                        │
│    """Schema: INFERRED (quality: low, 15 obs)"""             │
│    # Returns Pydantic model with Optional fields             │
│                                                              │
│  ┌────────────────────────────────────────────┐             │
│  │ After 100+ observations                    │             │
│  │ Quality reaches HIGH                       │             │
│  │ Wrapper auto-regenerates ↓                 │             │
│  └────────────────────────────────────────────┘             │
│                                                              │
│  Day 30: High Quality Schema                                 │
│  ────────────────────────                                    │
│  async def tool(params) → ToolResult:                        │
│    """Schema: INFERRED (quality: HIGH, 120 obs)"""           │
│    # Full Pydantic model, high confidence types              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
          │
          ▼
    ┌──────────────────────────┐
    │  Agent Script            │
    │  ─────────────────────   │
    │  result = await tool()   │
    │  print(result.field)     │  ◄── 40 tokens (73% reduction)
    └──────────────────────────┘

Benefits:
  ✓ Types improve automatically with usage
  ✓ Single source of truth for type knowledge
  ✓ Discovery integrated into generation
  ✓ Quality metrics always available
  ✓ Zero manual maintenance
```

---

## Diagram 3: Type Quality Progression

```
┌────────────────────────────────────────────────────────────────────┐
│                    Schema Quality Lifecycle                        │
└────────────────────────────────────────────────────────────────────┘

  Time ──────────────────────────────────────────────────────────────▶

  ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
  │  NONE    │ ───▶ │   LOW    │ ───▶ │  MEDIUM  │ ───▶ │   HIGH   │
  └──────────┘      └──────────┘      └──────────┘      └──────────┘
       │                  │                 │                  │
       │                  │                 │                  │
  0 obs            1-9 obs           10-99 obs          100+ obs
  No data          Initial          Consistent         Highly
  available        patterns         structure          reliable
       │                  │                 │                  │
       ▼                  ▼                 ▼                  ▼
  ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
  │ Helper   │      │ Inferred │      │ Inferred │      │ Strong   │
  │ Wrapper  │      │ Model    │      │ Model    │      │ Types    │
  │          │      │          │      │          │      │          │
  │ .get()   │      │ Optional │      │ Optional │      │ Required │
  │ .has()   │      │ fields   │      │ + better │      │ fields   │
  │ .require │      │ marked   │      │ types    │      │ + high   │
  │   ()     │      │ Optional │      │          │      │ confidence│
  └──────────┘      └──────────┘      └──────────┘      └──────────┘

                   AUTO-REGENERATION TRIGGERS
                            │     │
                            ▼     ▼
                    Quality level increases
                    Wrapper regenerates automatically
                    Developer sees better types in IDE
```

---

## Diagram 4: Wrapper Generation Strategy Decision Tree

```
┌────────────────────────────────────────────────────────────────────┐
│              Wrapper Generation Decision Logic                     │
└────────────────────────────────────────────────────────────────────┘

                        Tool Definition
                              │
                              ▼
                    ┌─────────────────┐
                    │ Has outputSchema│
                    │   declared?     │
                    └─────────────────┘
                      │             │
                  Yes │             │ No
                      │             │
            ┌─────────┘             └──────────┐
            ▼                                  ▼
   ┌──────────────────┐           ┌────────────────────┐
   │ DECLARED SCHEMA  │           │ Check Type Registry│
   │                  │           │ for observations   │
   └──────────────────┘           └────────────────────┘
            │                                  │
            │                                  ▼
            │                      ┌────────────────────┐
            │                      │ Quality >= HIGH?   │
            │                      └────────────────────┘
            │                         │              │
            │                     Yes │              │ No
            │                         │              │
            ▼                         ▼              ▼
   ┌──────────────────┐     ┌──────────────┐  ┌─────────────┐
   │ Generate TYPED   │     │ Generate     │  │ Generate    │
   │ Wrapper          │     │ INFERRED     │  │ HELPER      │
   │                  │     │ Wrapper      │  │ Wrapper     │
   │ Full Pydantic    │     │              │  │             │
   │ model with       │     │ Pydantic     │  │ Response    │
   │ validation       │     │ model with   │  │ class with  │
   │                  │     │ warnings     │  │ safe        │
   │ Return:          │     │              │  │ accessors   │
   │   ToolResult     │     │ Return:      │  │             │
   │                  │     │   ToolResult │  │ Return:     │
   │ Quality: HIGH    │     │              │  │   Response  │
   │ Source: DECLARED │     │ Quality: HIGH│  │   Helper    │
   └──────────────────┘     │ Source:      │  │             │
                            │   INFERRED   │  │ Quality:    │
                            └──────────────┘  │   NONE-MED  │
                                              │ Source:     │
                                              │   UNKNOWN   │
                                              └─────────────┘

Example Outputs:

DECLARED:                   INFERRED:                    HELPER:
─────────                   ─────────                    ───────

async def tool(             async def tool(              class ToolResponse:
  params: Params            params: Params                def get(k, default)
) -> ToolResult:            ) -> ToolResult:              def has(k)
  """                         """                          def require(k)
  Schema: DECLARED            Schema: INFERRED             @property raw
  Quality: HIGH               Quality: HIGH
  """                         Obs: 120                   async def tool(
  ...                         WARNING: Inferred           params: Params
  return ToolResult           """                        ) -> ToolResponse:
    .model_validate(...)      ...                          """
                              return ToolResult            Schema: UNKNOWN
                                .model_validate(...)       Will improve!
                                                           """
                                                           ...
                                                           return ToolResponse(...)
```

---

## Diagram 5: Integration Workflow

```
┌────────────────────────────────────────────────────────────────────┐
│         Complete Workflow: Generation → Discovery → Evolution      │
└────────────────────────────────────────────────────────────────────┘

Developer runs: uv run mcp-generate
       │
       ▼
┌──────────────────────────────────────────┐
│ Phase 1: Connect to MCP Servers          │
│ ──────────────────────────────           │
│ • Read mcp_config.json                   │
│ • Connect to each server                 │
│ • Call list_tools()                      │
└──────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Phase 2: Register Tools in Type Registry │
│ ──────────────────────────────           │
│ For each tool:                           │
│ • Extract inputSchema (always present)   │
│ • Extract outputSchema (if present)      │
│ • Create ToolTypeInfo                    │
│ • Set quality = HIGH if declared         │
│ • Set quality = NONE if missing          │
│ • Persist to .mcp_runtime/registry.json  │
└──────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Phase 3: Generate Wrappers               │
│ ──────────────────────────────           │
│ For each tool:                           │
│ • Generate params model (always)         │
│ • Check registry for quality             │
│ • Choose wrapper strategy:               │
│   ├─ Declared → Typed wrapper            │
│   ├─ High quality → Inferred wrapper     │
│   └─ Unknown → Helper wrapper            │
│ • Write to servers/{server}/{tool}.py    │
└──────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Phase 4: Optional Discovery              │
│ ──────────────────────────────           │
│ If discovery_config.json exists:         │
│ • Execute configured safe tools          │
│ • Capture responses                      │
│ • Call registry.observe_execution()      │
│ • Update quality metrics                 │
└──────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Phase 5: Regenerate Improved Tools       │
│ ──────────────────────────────           │
│ Schema Evolution Manager:                │
│ • Check which tools improved quality     │
│ • Regenerate wrappers for improved tools │
│ • Update last_generated tracking         │
└──────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Phase 6: Quality Report                  │
│ ──────────────────────────────           │
│ Print metrics:                           │
│ • Total tools: 42                        │
│ • Declared: 18 (42.9%)                   │
│ • Inferred: 12 (28.6%)                   │
│ • Unknown: 12 (28.6%)                    │
│ • High quality: 30 (71.4%)               │
└──────────────────────────────────────────┘
       │
       ▼
   ✓ Complete!

─────────────────────────────────────────────────────────────────────

Agent runs script with harness
       │
       ▼
┌──────────────────────────────────────────┐
│ Runtime: Continuous Learning             │
│ ──────────────────────────────           │
│ Every tool execution:                    │
│ • Call tool via MCP                      │
│ • Defensive unwrapping                   │
│ • registry.observe_execution()           │
│   ├─ Increment observation count         │
│   ├─ Infer field types                   │
│   ├─ Track consistency                   │
│   └─ Update quality level                │
│ • Return result to script                │
└──────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Background: Evolution Task               │
│ ──────────────────────────────           │
│ Every 5 minutes:                         │
│ • Check for quality improvements         │
│ • Regenerate improved wrappers           │
│ • Log improvements                       │
└──────────────────────────────────────────┘
```

---

## Diagram 6: Data Flow - Type Registry

```
┌────────────────────────────────────────────────────────────────────┐
│                  Type Registry Data Model                          │
└────────────────────────────────────────────────────────────────────┘

File: .mcp_runtime/type_registry.json

{
  "git__git_status": {                    ◄── Tool ID
    "tool_id": "git__git_status",
    "server_name": "git",
    "tool_name": "git_status",

    "source": "inferred",                 ◄── DECLARED | INFERRED | HYBRID
    "quality": "high",                    ◄── NONE | LOW | MEDIUM | HIGH

    "input_schema": { ... },              ◄── Always present (MCP requirement)
    "output_schema": null,                ◄── May be null

    "observation_count": 125,             ◄── Execution count
    "last_observed": "2025-11-08T10:30:00",

    "inferred_fields": {                  ◄── Learned from responses
      "status": "str",
      "branch": "str",
      "ahead": "int",
      "behind": "int",
      "files": "List[Dict[str, Any]]"
    },

    "field_consistency": {                ◄── Confidence scores
      "status": 1.0,      // 100% consistent
      "branch": 1.0,
      "ahead": 0.9,       // 90% consistent
      "behind": 0.9,
      "files": 0.85       // 85% consistent
    }
  },

  "fetch__fetch": {
    "tool_id": "fetch__fetch",
    "server_name": "fetch",
    "tool_name": "fetch",

    "source": "declared",                 ◄── Has outputSchema
    "quality": "high",

    "input_schema": { ... },
    "output_schema": { ... },             ◄── Provided by server

    "observation_count": 0,               ◄── No observations needed
    "last_observed": null,

    "inferred_fields": {},                ◄── Empty (not needed)
    "field_consistency": {}
  }
}

┌────────────────────────────────────────────────────────────────────┐
│                    Quality Calculation Logic                       │
└────────────────────────────────────────────────────────────────────┘

def calculate_quality(tool_info: ToolTypeInfo) -> SchemaQuality:
    if tool_info.source == "declared":
        return SchemaQuality.HIGH  # Trust declared schemas

    # For inferred schemas, use observation count
    if tool_info.observation_count >= 100:
        # Also check field consistency
        avg_consistency = mean(tool_info.field_consistency.values())
        if avg_consistency >= 0.8:
            return SchemaQuality.HIGH
        else:
            return SchemaQuality.MEDIUM

    elif tool_info.observation_count >= 10:
        return SchemaQuality.MEDIUM

    elif tool_info.observation_count >= 1:
        return SchemaQuality.LOW

    else:
        return SchemaQuality.NONE
```

---

## Diagram 7: Before/After Comparison - Developer Experience

```
┌────────────────────────────────────────────────────────────────────┐
│                    Developer Experience: BEFORE                    │
└────────────────────────────────────────────────────────────────────┘

1. Generate wrappers
   $ uv run mcp-generate
   ✓ Generated git server wrappers

2. Check wrapper code
   $ cat servers/git/git_status.py

   async def git_status(params: GitStatusParams) -> Dict[str, Any]:
       """Get git repository status"""
       ...                                    ◄── No type hints for output

3. Write agent script
   result = await call_mcp_tool("git__git_status", {"repo_path": "."})

   # Agent must defensively handle result
   if isinstance(result, dict):              ◄── Type guard
       status = result.get("status")         ◄── Safe accessor
       if status:                            ◄── Existence check
           print(f"Status: {status}")
       else:                                 ◄── Fallback
           print("No status available")

       files = result.get("files", [])       ◄── Default value
       if isinstance(files, list):           ◄── Type guard
           for file in files:
               if isinstance(file, dict):    ◄── Type guard
                   path = file.get("path", "unknown")
                   print(f"  {path}")
   else:
       print("Unexpected response type")    ◄── Error handling

   Token count: ~150 tokens
   IDE support: None
   Type safety: None

4. Want better types?
   $ # Must manually create discovery_config.json
   $ # Must manually run discovery
   $ uv run mcp-discover
   $ # Must manually copy discovered types
   $ # Must manually update wrapper imports

   Time: 15-30 minutes per server

─────────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────┐
│                    Developer Experience: AFTER                     │
└────────────────────────────────────────────────────────────────────┘

1. Generate wrappers (with automatic discovery)
   $ uv run mcp-generate
   ✓ Generated git server wrappers
   ✓ Discovered schemas for 3 safe tools
   ✓ Schema quality: 18/42 tools HIGH (42.9%)

2. Check wrapper code
   $ cat servers/git/git_status.py

   class GitStatusResponse:                ◄── Helper wrapper
       def get(self, key, default=None)
       def has(self, key)
       def require(self, key)
       @property raw

   async def git_status(
       params: GitStatusParams
   ) -> GitStatusResponse:                 ◄── Better return type
       """
       Get git repository status
       Schema: UNKNOWN (will improve with usage)  ◄── Clear expectation
       """

3. Write agent script
   response = await git_status(GitStatusParams(repo_path="."))

   # Use safe accessors (no type guards needed)
   status = response.get("status", "unknown")    ◄── One line
   print(f"Status: {status}")

   if response.has("files"):                     ◄── Clear check
       files = response.require("files")         ◄── Explicit requirement
       for file in files:
           print(file.get("path", "unknown"))

   Token count: ~45 tokens (70% reduction)
   IDE support: Method autocomplete
   Type safety: Runtime safety via helpers

4. After 100+ executions (automatic)
   $ # No action needed - wrappers improve automatically
   $ cat servers/git/git_status.py

   class GitStatusResult(BaseModel):       ◄── Auto-generated!
       """
       Schema: INFERRED (quality: HIGH)
       Observations: 125
       """
       status: str
       branch: str
       ahead: Optional[int] = None
       behind: Optional[int] = None
       files: Optional[List[Dict[str, Any]]] = None

   async def git_status(
       params: GitStatusParams
   ) -> GitStatusResult:                   ◄── Full type safety!

5. Updated agent script (same code works better!)
   result = await git_status(GitStatusParams(repo_path="."))
   print(f"Status: {result.status}")       ◄── IDE autocomplete!
   print(f"Branch: {result.branch}")       ◄── Type checking!
   if result.files:
       for file in result.files:
           print(file)

   Token count: ~40 tokens (73% reduction)
   IDE support: Full autocomplete
   Type safety: Pydantic validation

   Time to improve: Automatic (0 manual work)
```

---

## Diagram 8: System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      System Architecture                            │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                         MCP Servers Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │   Git    │  │  Fetch   │  │  GitHub  │  │   ADO    │  ...       │
│  │  Server  │  │  Server  │  │  Server  │  │  Server  │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└──────────────────────────────────────────────────────────────────────┘
        │               │               │               │
        └───────────────┴───────────────┴───────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     MCP Client Layer                                 │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  McpClientManager (mcp_client.py)                          │     │
│  │  ─────────────────────────────────────────────────────     │     │
│  │  • Lazy server connections                                 │     │
│  │  • Tool execution                                          │     │
│  │  • Defensive unwrapping                                    │     │
│  │  • Observation recording  ─────────┐                       │     │
│  └────────────────────────────────────│───────────────────────┘     │
└────────────────────────────────────────│──────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   Type Intelligence Layer (NEW)                      │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  Type Registry (type_registry.py)                          │     │
│  │  ─────────────────────────────────                         │     │
│  │  Persistent Storage: .mcp_runtime/type_registry.json       │     │
│  │                                                             │     │
│  │  For each tool:                                            │     │
│  │  • Input/output schemas                                    │     │
│  │  • Schema source (declared/inferred/hybrid)                │     │
│  │  • Quality level (none/low/medium/high)                    │     │
│  │  • Observation count                                       │     │
│  │  • Inferred field types                                    │     │
│  │  • Field consistency scores                                │     │
│  └────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
        │                           │                        │
        ▼                           ▼                        ▼
┌─────────────┐         ┌─────────────────┐      ┌──────────────────┐
│ Wrapper     │         │ Schema          │      │ Discovery        │
│ Generator   │         │ Evolution       │      │ Integration      │
│ ────────    │         │ ─────────       │      │ ────────────     │
│ Queries     │         │ Background      │      │ Auto-execute     │
│ registry    │         │ task checks     │      │ safe tools       │
│ for quality │         │ for quality     │      │ during           │
│             │         │ improvements    │      │ generation       │
│ Generates   │         │                 │      │                  │
│ adaptive    │         │ Triggers        │      │ Populates        │
│ wrappers    │         │ regeneration    │      │ registry         │
│ based on    │         │ when threshold  │      │ with initial     │
│ schema      │         │ reached         │      │ observations     │
│ availability│         │                 │      │                  │
└─────────────┘         └─────────────────┘      └──────────────────┘
        │                           │                        │
        └───────────────────────────┴────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Generated Wrappers Layer                          │
│  servers/                                                            │
│    git/                                                              │
│      git_status.py    ◄── Typed/Inferred/Helper (adaptive)          │
│      git_log.py       ◄── Types improve automatically               │
│    fetch/                                                            │
│      fetch.py         ◄── Quality metadata in docstrings            │
│    github/                                                           │
│      search_code.py   ◄── Schema source visible                     │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      Script Execution Layer                          │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  Harness (harness.py)                                      │     │
│  │  ────────────────────                                      │     │
│  │  • Runs user scripts                                       │     │
│  │  • Manages MCP lifecycle                                   │     │
│  │  • Background evolution task (optional)                    │     │
│  │  • Graceful shutdown                                       │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  User Script:                                                        │
│  ────────────                                                        │
│  result = await git_status(...)                                     │
│  print(result.status)  ◄── Type-safe (eventually)                   │
└──────────────────────────────────────────────────────────────────────┘

Key Data Flows:
  1. Wrapper generation reads registry for quality decisions
  2. Tool execution writes observations to registry
  3. Evolution task reads registry, regenerates wrappers
  4. Discovery writes initial observations during setup
```

---

**End of Diagrams**

These diagrams illustrate the transformation from scattered, static type handling to a unified, self-improving architecture that learns from usage and automatically enhances developer experience over time.
