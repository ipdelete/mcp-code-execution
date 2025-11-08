# MCP Code Execution - Python Port Tasks

---
feature: Python Port of MCP Code Execution Runtime
generated: 2025-11-07
total_tasks: 85
checklist_validation: CHECKLIST.md (135 quality checks)
plan_version: 3.0
branch: python-port
---

## Implementation Strategy

**MVP Scope**: Phase 0 (PoC) + Phase 1 (Setup) + Phase 2 (MCP Client) + Phase 3 (Harness) + Phase 5 (Wrapper Gen) + Phase 7 (Integration Tests)

**Critical Path**: Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 7 → Phase 8

**Parallel Execution Opportunities**:
- Phase 1: Project setup tasks can run in parallel
- Phase 2: Tests can be written while implementing client
- Phase 8: Documentation tasks can run in parallel

**Go/No-Go Decision**: Phase 0 PoC must succeed before proceeding to Phase 1.

---

## Phase 0: Proof of Concept (CRITICAL BLOCKER)

**Goal**: Validate Python MCP SDK compatibility before committing to architecture

**Success Criteria** (CHK011-CHK014):
- ✅ stdio transport works with Python SDK
- ✅ Connection lifecycle validated
- ✅ Response structure matches expectations
- ✅ Both git and fetch servers tested

### Tasks

- [x] T001 Install Python MCP SDK dependencies in temporary test environment: `uv pip install mcp`
- [x] T002 Create PoC script at `poc_mcp_test.py` with git server connection test
- [x] T003 Validate stdio transport connection to git server (@modelcontextprotocol/server-git)
- [x] T004 Test Client initialization and list_tools() response format
- [x] T005 Test tool calling with git_status (repo_path: ".")
- [x] T006 Validate response unwrapping pattern (check for .content attribute)
- [x] T007 Test connection lifecycle (connect → initialize → call → close)
- [x] T008 Repeat validation with fetch server (@modelcontextprotocol/server-fetch)
- [x] T009 Document any differences from TypeScript SDK in `poc_findings.md`
- [x] T010 Validate response structure matches defensive unwrapping expectations
- [x] T011 **GO/NO-GO DECISION**: Document PoC validation results and decision to proceed

**Validation**: CHK011-CHK015

---

## Phase 1: Project Setup & Structure

**Goal**: Set up complete Python project with modern tooling (uv + src/ layout)

**Success Criteria** (CHK016-CHK022):
- ✅ pyproject.toml with all dependencies
- ✅ src/ layout following Python best practices
- ✅ Error handling infrastructure
- ✅ Config validation with Pydantic

### Tasks

- [x] T012 [P] Move TypeScript files to `_typescript_reference/runtime/` for reference
- [x] T013 [P] Move TypeScript test files to `_typescript_reference/tests/`
- [x] T014 [P] Initialize uv project: `uv init --lib --name mcp-execution`
- [x] T015 [P] Pin Python version: `uv python pin 3.11` and create `.python-version`
- [x] T016 Create `pyproject.toml` with project metadata and dependencies (mcp>=1.0.0, pydantic>=2.0.0, aiofiles>=23.0.0)
- [x] T017 Add dev dependencies to `pyproject.toml` (black>=24.0.0, mypy>=1.8.0, ruff>=0.2.0, pytest>=8.0.0, pytest-asyncio>=0.23.0)
- [x] T018 Configure black in `pyproject.toml` (line-length = 100)
- [x] T019 Configure mypy in `pyproject.toml` (strict = true, python_version = "3.11")
- [x] T020 Configure ruff in `pyproject.toml` (line-length = 100, target-version = "py311")
- [x] T021 [P] Update `.gitignore` for Python artifacts (__pycache__, *.pyc, .pytest_cache/, .mypy_cache/, .ruff_cache/, *.egg-info/, dist/, build/, .uv/, .venv/)
- [x] T022 [P] Create directory structure: `mkdir -p src/runtime src/servers tests/unit tests/integration workspace`
- [x] T023 [P] Create package markers: `touch src/runtime/__init__.py src/servers/__init__.py tests/__init__.py`
- [x] T024 Create error hierarchy in `src/runtime/exceptions.py` (McpExecutionError, ServerConnectionError, ToolNotFoundError, ToolExecutionError, ConfigurationError, SchemaValidationError)
- [x] T025 Create config models in `src/runtime/config.py` (ServerConfig, McpConfig with Pydantic)
- [x] T026 Run `uv sync` to generate uv.lock file
- [x] T027 Install project in editable mode with dev dependencies: `uv pip install -e ".[dev]"`
- [x] T028 Validate project structure: verify all directories and files exist

**Validation**: CHK016-CHK022, CHK104-CHK111

---

## Phase 2: Core Runtime - MCP Client Manager

**Goal**: Port the lazy-loading MCP client manager (98.7% token reduction pattern)

**Success Criteria** (CHK023-CHK032):
- ✅ Lazy initialization (config loaded, servers NOT connected)
- ✅ Lazy connection (connect on first tool call)
- ✅ Tool caching implemented
- ✅ Defensive unwrapping
- ✅ Singleton pattern

### Tasks

- [x] T029 Create `src/runtime/mcp_client.py` with McpClientManager class skeleton
- [x] T030 Implement `__init__` method with internal state (_clients, _tool_cache, _config, _initialized)
- [x] T031 Implement `initialize()` method: load config from mcp_config.json using aiofiles
- [x] T032 Implement Pydantic config validation in initialize() using McpConfig.model_validate_json()
- [x] T033 Implement `_connect_to_server()` method with stdio_client and StdioServerParameters
- [x] T034 Implement lazy connection logic: only connect when tool is first called
- [x] T035 Implement tool identifier parsing (format: "serverName__toolName")
- [x] T036 Implement `call_tool()` method with lazy connection and defensive unwrapping (getattr(result, 'value', result))
- [x] T037 Implement JSON parsing for text responses in call_tool()
- [x] T038 Implement `list_all_tools()` method (connects to all servers)
- [x] T039 Implement tool caching to avoid repeated list_tools() calls
- [x] T040 Implement `cleanup()` method with proper error handling for all connections
- [x] T041 Implement singleton pattern using @lru_cache decorator on get_mcp_client_manager()
- [x] T042 Implement convenience function `call_mcp_tool()` that uses singleton manager
- [x] T043 Add logging statements (INFO level for connections, DEBUG for details)
- [x] T044 Add proper error handling with custom exceptions from exceptions.py
- [x] T045 [P] Create unit tests in `tests/test_mcp_client.py` for lazy initialization
- [x] T046 [P] Add unit test for lazy connection (verify server connects on first call, not on initialize)
- [x] T047 [P] Add unit test for tool caching
- [x] T048 [P] Add unit test for cleanup/shutdown
- [x] T049 Run unit tests: `uv run pytest tests/test_mcp_client.py`

**Validation**: CHK023-CHK032, CHK086-CHK089, CHK097, CHK112-CHK120

---

## Phase 3: Script Execution Harness

**Goal**: CLI entry point for executing Python scripts with MCP support

**Success Criteria** (CHK033-CHK041):
- ✅ CLI argument parsing
- ✅ Signal handlers (async-safe)
- ✅ Script execution with runpy
- ✅ Proper cleanup

### Tasks

- [x] T050 Create `src/runtime/harness.py` with main() async function
- [x] T051 Implement CLI argument parsing (script_path from sys.argv[1])
- [x] T052 Implement script path validation (check file exists)
- [x] T053 Implement sys.path management: add src/ to sys.path for imports
- [x] T054 Implement MCP client manager initialization
- [x] T055 Implement signal handlers for SIGINT and SIGTERM using asyncio.Event (not async/await)
- [x] T056 Implement script execution using runpy.run_path() in isolated namespace
- [x] T057 Implement try/except/finally for error handling and cleanup
- [x] T058 Implement proper exit codes (0=success, 1=error, 130=Ctrl+C)
- [x] T059 Configure logging to stderr with "[LEVEL] message" format
- [x] T060 Implement cleanup guarantee in finally block with error handling
- [x] T061 Add `__name__ == "__main__"` block with asyncio.run(main())
- [x] T062 Test harness execution: `uv run python -m runtime.harness workspace/test_script.py`
- [x] T063 Add script alias to `pyproject.toml`: mcp-exec = "runtime.harness:main"
- [x] T064 Verify Ctrl+C handling (exit code 130)

**Validation**: CHK033-CHK041, CHK117-CHK118

---

## Phase 4: Field Normalization

**Goal**: Normalize inconsistent field casing from different APIs

**Success Criteria** (CHK042-CHK048):
- ✅ Pluggable normalization strategies
- ✅ Recursive traversal
- ✅ Immutability
- ✅ Configuration-driven

### Tasks

- [x] T065 Create `src/runtime/normalize_fields.py` with NormalizationStrategy Literal type
- [x] T066 Create NormalizationConfig Pydantic model
- [x] T067 Define NORMALIZATION_CONFIG with default strategies (ado: "ado-pascal-case", filesystem: "none", github: "none")
- [x] T068 Implement `normalize_field_names()` function with strategy dispatch
- [x] T069 Implement `normalize_ado_fields()` function with ADO-specific rules (system.* → System.*, microsoft.* → Microsoft.*, custom.* → Custom.*, wef_* → WEF_*)
- [x] T070 Implement recursive traversal for dicts and lists
- [x] T071 Ensure immutability (return new objects, don't mutate)
- [x] T072 [P] Create unit tests in `tests/test_normalize_fields.py` for ADO normalization
- [x] T073 [P] Add unit test for recursion with nested structures
- [x] T074 [P] Add unit test for immutability (original unchanged)
- [x] T075 Run unit tests: `uv run pytest tests/test_normalize_fields.py`

**Validation**: CHK042-CHK048, CHK099

---

## Phase 5: Wrapper Generation

**Goal**: Generate typed Python wrappers from MCP server tool definitions

**Success Criteria** (CHK049-CHK062):
- ✅ JSON Schema → Pydantic conversion
- ✅ Complete type mapping
- ✅ Defensive unwrapping in generated code
- ✅ Field normalization integration

### Tasks

- [x] T076 Create `src/runtime/schema_utils.py` for JSON Schema utilities
- [x] T077 Implement `json_schema_to_pydantic_field()` function: handle string, number, integer, boolean, null types
- [x] T078 Add support for array types with items schema
- [x] T079 Add support for object types with properties (generate nested Pydantic models)
- [x] T080 Add support for additionalProperties (Dict[str, T])
- [x] T081 Add support for enum constraints (Literal types)
- [x] T082 Add support for union types (["string", "null"] → Optional[str])
- [x] T083 Add support for required vs optional fields
- [x] T084 Implement `generate_pydantic_model()` function for creating model classes
- [x] T085 Create `src/runtime/generate_wrappers.py` with main generation logic
- [x] T086 Implement `generate_tool_wrapper()` function: create async function with type hints
- [x] T087 Add docstring generation from tool descriptions in generate_tool_wrapper()
- [x] T088 Add defensive unwrapping in generated wrappers (getattr(result, 'value', result))
- [x] T089 Integrate field normalization into generate_tool_wrapper()
- [x] T090 Implement `generate_wrappers()` main orchestrator: load mcp_config.json
- [x] T091 Add logic to connect to each server and call list_tools()
- [x] T092 Add logic to generate wrappers for each tool: write to servers/{server}/{tool}.py
- [x] T093 Implement __init__.py barrel export generation for each server
- [x] T094 Implement per-server README.md generation
- [x] T095 Add logic to preserve custom utils.py files (don't overwrite)
- [x] T096 Add `__name__ == "__main__"` block with asyncio.run(generate_wrappers())
- [x] T097 Add script alias to `pyproject.toml`: mcp-generate = "runtime.generate_wrappers:main"
- [x] T098 Test generation with git server: `uv run python -m runtime.generate_wrappers`
- [x] T099 Verify generated Pydantic models are valid: `uv run mypy src/servers/`
- [x] T100 [P] Create unit tests in `tests/test_generate_wrappers.py` for schema conversion
- [x] T101 [P] Add unit test for type mapping completeness
- [x] T102 Run unit tests: `uv run pytest tests/test_generate_wrappers.py`

**Validation**: CHK049-CHK062, CHK098, CHK100

---

## Phase 6: Schema Discovery (OPTIONAL - P1)

**Goal**: Generate Pydantic models from actual API responses

**Success Criteria** (CHK063-CHK071):
- ✅ Safe tool execution only
- ✅ Type inference from responses
- ✅ All fields optional (defensive)

### Tasks

- [x] T103 Create `discovery_config.example.json` at root with safe tool examples
- [x] T104 Create `src/runtime/discover_schemas.py` with main discovery logic
- [x] T105 Implement config loading from discovery_config.json
- [x] T106 Implement safe tool execution (read-only operations only)
- [x] T107 Implement response capture and unwrapping (.value)
- [x] T108 Implement `infer_pydantic_model_from_response()` function: handle str, int, float, bool, list, dict, None
- [x] T109 Add array handling: use first element as template
- [x] T110 Mark all discovered fields as Optional by default
- [x] T111 Add metadata preservation (tool description, sample params)
- [x] T112 Add warning comments about defensive coding in generated files
- [x] T113 Write discovered types to servers/{server}/discovered_types.py
- [x] T114 Add `__name__ == "__main__"` block with asyncio.run(discover_schemas())
- [x] T115 Add script alias to `pyproject.toml`: mcp-discover = "runtime.discover_schemas:main"
- [x] T116 Test discovery with safe GitHub tool: `uv run python -m runtime.discover_schemas`

**Validation**: CHK063-CHK071

---

## Phase 7: Integration Testing & Example Script

**Goal**: Validate end-to-end functionality with real MCP servers

**Success Criteria** (CHK072-CHK078):
- ✅ Integration tests with git and fetch servers
- ✅ Example demonstrates 98.7% token reduction
- ✅ End-to-end validation

### Tasks

- [ ] T117 Create `mcp_config.json` at root with git and fetch server configurations
- [ ] T118 Create `tests/integration/test_git_server.py` with test_git_status() test
- [ ] T119 Implement git_status integration test: verify connection and response structure
- [ ] T120 Create `tests/integration/test_fetch_server.py` with test_fetch_url() test
- [ ] T121 Implement fetch_url integration test: verify content retrieval
- [ ] T122 Create `tests/integration/test_harness_integration.py` for script execution tests
- [ ] T123 Create `workspace/example_progressive_disclosure.py` ported from TypeScript version
- [ ] T124 Implement example: list directory, filter TypeScript files, count files with 'async'
- [ ] T125 Add local data processing in example (demonstrate pattern)
- [ ] T126 Add summary-only output (not raw file contents)
- [ ] T127 Test example execution: `uv run python -m runtime.harness workspace/example_progressive_disclosure.py`
- [ ] T128 Verify example demonstrates 98.7% token reduction pattern
- [ ] T129 Run all integration tests: `uv run pytest tests/integration/`

**Validation**: CHK072-CHK078, CHK101-CHK103

---

## Phase 8: Documentation & Polish

**Goal**: Complete Python-specific documentation

**Success Criteria** (CHK079-CHK085):
- ✅ README updated for Python
- ✅ Python-specific docs created
- ✅ Development setup documented

### Tasks

- [x] T130 [P] Update README.md: add Python installation section (uv installation)
- [x] T131 [P] Add Python quick start guide to README.md
- [x] T132 [P] Update examples in README.md to show Python usage
- [x] T133 [P] Document Python-specific patterns in README.md
- [x] T134 [P] Add note about Python port to README.md
- [x] T135 [P] Create `docs/python-port.md` documenting differences from TypeScript
- [x] T136 [P] Create `docs/pydantic-usage.md` with Pydantic model usage examples
- [x] T137 [P] Create `docs/type-safety.md` with Python type hints and mypy usage
- [x] T138 Add project.scripts section to `pyproject.toml` (mcp-exec, mcp-generate, mcp-discover)
- [x] T139 Create or update `package.json` with npm compatibility scripts (generate, discover-schemas, exec)
- [x] T140 Document development setup in README.md: uv sync, mypy, black, ruff, pytest commands
- [x] T141 Add contribution guidelines for Python development
- [x] T142 Run full test suite: `uv run pytest`
- [x] T143 Run type checking: `uv run mypy src/`
- [x] T144 Run code formatting check: `uv run black --check src/ tests/`
- [x] T145 Run linting: `uv run ruff check src/ tests/`
- [x] T146 Format all code: `uv run black src/ tests/`

**Validation**: CHK079-CHK085, CHK093-CHK096, CHK137-CHK145

---

## Final Validation & Merge

**Goal**: Validate all success criteria and merge to master

### Tasks

- [ ] T147 Verify all Phase 0 PoC deliverables complete (CHK011-CHK015)
- [ ] T148 Verify all Phase 1 setup deliverables complete (CHK016-CHK022)
- [ ] T149 Verify all Phase 2 MCP client deliverables complete (CHK023-CHK032)
- [ ] T150 Verify all Phase 3 harness deliverables complete (CHK033-CHK041)
- [ ] T151 Verify all Phase 4 normalization deliverables complete (CHK042-CHK048)
- [ ] T152 Verify all Phase 5 wrapper generation deliverables complete (CHK049-CHK062)
- [ ] T153 Verify all Phase 7 integration testing deliverables complete (CHK072-CHK078)
- [ ] T154 Verify all Phase 8 documentation deliverables complete (CHK079-CHK085)
- [ ] T155 Run complete checklist validation: verify all 135 CHK items
- [ ] T156 Verify success criteria: lazy loading pattern preserved (CHK086-CHK089)
- [ ] T157 Verify success criteria: type safety complete (CHK090-CHK092)
- [ ] T158 Verify success criteria: quality standards met (CHK093-CHK096)
- [ ] T159 Create commit: "feat: Complete Python port of MCP Code Execution runtime"
- [ ] T160 Remove TypeScript reference: `git rm -rf _typescript_reference/`
- [ ] T161 Create commit: "chore: Remove TypeScript implementation, Python port complete"
- [ ] T162 Merge python-port branch to master: `git checkout master && git merge python-port`
- [ ] T163 Tag release: `git tag v2.0.0-python`
- [ ] T164 Push to remote: `git push origin master --tags`

**Validation**: All CHK items (CHK001-CHK135)

---

## Summary

**Total Tasks**: 164 (85 implementation + 79 validation)
**Estimated Time**: 26-37 hours focused development
**Minimum Viable Port (P0)**: Tasks T001-T164 (excluding Phase 6)

**Parallel Execution Opportunities**:
- Phase 1: T012-T013, T021-T023 (setup tasks)
- Phase 2: T045-T048 (tests parallel to implementation)
- Phase 4: T072-T074 (tests parallel to implementation)
- Phase 5: T100-T101 (tests parallel to implementation)
- Phase 8: T130-T137 (documentation tasks)

**Task Dependencies**:
```
Phase 0 (T001-T011) → BLOCKER for all other phases
Phase 1 (T012-T028) → Required for Phase 2, 3, 4, 5
Phase 2 (T029-T049) → Required for Phase 3, 5, 7
Phase 3 (T050-T064) → Required for Phase 7
Phase 4 (T065-T075) → Required for Phase 5
Phase 5 (T076-T102) → Required for Phase 7
Phase 6 (T103-T116) → Optional, can run after Phase 5
Phase 7 (T117-T129) → Required for Phase 8
Phase 8 (T130-T146) → Can start early, complete last
Final (T147-T164) → Requires all phases complete
```

**Independent Test Criteria**:
- Each phase has dedicated test tasks marked [P] for parallel execution
- Integration tests in Phase 7 validate end-to-end functionality
- Final validation phase (T147-T164) uses CHECKLIST.md for comprehensive QA

**Checklist Cross-Reference**:
- Every task maps to specific CHK items from CHECKLIST.md
- 135 quality checks validate plan completeness
- Use checklist as acceptance criteria for phase completion

**Next Action**: Begin Phase 0 (T001-T011) to validate Python MCP SDK compatibility.
