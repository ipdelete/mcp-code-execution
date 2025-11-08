# Implementation Reference Guide

**Quick reference for implementing the output schema solution**

---

## File Checklist

### New Files to Create

```
src/runtime/
├── type_registry.py           # ~400 lines - Core registry implementation
└── schema_evolution.py        # ~300 lines - Auto-regeneration logic

.mcp_runtime/
└── type_registry.json         # Auto-generated - Persistent storage

tests/unit/
├── test_type_registry.py      # ~500 lines - Registry tests
├── test_smart_wrappers.py     # ~400 lines - Wrapper generation tests
└── test_schema_evolution.py   # ~300 lines - Evolution tests

tests/integration/
├── test_learning_workflow.py  # ~300 lines - Full lifecycle tests
└── test_integrated_workflow.py # ~200 lines - End-to-end tests

docs/
└── SCHEMA_GUIDE.md            # User documentation
```

### Files to Modify

```
src/runtime/
├── generate_wrappers.py       # Add: generate_wrappers_with_discovery()
│                               # Add: _generate_typed_wrapper()
│                               # Add: _generate_inferred_wrapper()
│                               # Add: _generate_dict_wrapper()
│                               # Modify: generate_tool_wrapper() to call above
│
├── mcp_client.py              # Add: registry.observe_execution() after call_tool
│                               # Import: from .type_registry import get_type_registry
│
└── harness.py                 # Optional: Add background evolution task

pyproject.toml                  # Add: mcp-report = "runtime.type_registry:report_main"
                                # Add: mcp-evolve = "runtime.schema_evolution:evolve_main"

README.md                       # Add: Schema quality section
```

---

## Implementation Phases

### Phase 1: Type Registry (Week 1-2)

#### Day 1-3: Core Registry Implementation

**File**: `src/runtime/type_registry.py`

```python
# Key classes to implement:

class SchemaSource(str, Enum):
    DECLARED = "declared"
    INFERRED = "inferred"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"

class SchemaQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

class ToolTypeInfo(BaseModel):
    # 15 fields total - see architecture doc

class TypeRegistry:
    def __init__(self, storage_path: Path)
    def register_tool(...)
    def observe_execution(...)
    def get_tool_info(...)
    def get_quality_report(...)
    def _load_from_disk(...)
    def _persist(...)

def get_type_registry() -> TypeRegistry
```

**Test Coverage**:
- Registry persistence (save/load)
- Tool registration
- Observation recording
- Quality calculation
- Field consistency tracking

**Success Criteria**:
- [ ] Registry persists across sessions
- [ ] Quality metrics accurate
- [ ] All tests passing
- [ ] No performance regression

---

#### Day 4-5: Integration with Wrapper Generation

**File**: `src/runtime/generate_wrappers.py`

**Changes**:
```python
async def generate_wrappers(config_path: Path | None = None) -> None:
    registry = get_type_registry()  # ADD THIS

    for server_name, server_config in config.mcpServers.items():
        tools_response = await session.list_tools()

        for tool in tools_response.tools:
            # ADD THIS
            tool_id = f"{server_name}__{tool.name}"
            registry.register_tool(
                tool_id=tool_id,
                server_name=server_name,
                tool_name=tool.name,
                input_schema=tool.inputSchema,
                output_schema=tool.outputSchema
            )

            # Existing wrapper generation continues...
```

**Test Coverage**:
- Registration during generation
- Registry populated correctly
- Quality set correctly (HIGH for declared, NONE for missing)

**Success Criteria**:
- [ ] All tools registered during generation
- [ ] Registry file created in .mcp_runtime/
- [ ] Existing tests still pass

---

#### Day 6-7: Integration with Runtime Execution

**File**: `src/runtime/mcp_client.py`

**Changes**:
```python
from .type_registry import get_type_registry

async def call_tool(self, tool_identifier: str, params: dict[str, Any]) -> Any:
    # Existing execution code...
    result = await client.call_tool(tool_name, params)
    unwrapped = # ... defensive unwrapping ...

    # ADD THIS
    registry = get_type_registry()
    registry.observe_execution(tool_identifier, unwrapped)

    return unwrapped
```

**Test Coverage**:
- Observations recorded after execution
- Quality improves with observations
- No performance impact

**Success Criteria**:
- [ ] Every execution updates registry
- [ ] Observation count increments
- [ ] Quality transitions work (NONE → LOW → MEDIUM → HIGH)
- [ ] Integration tests pass

---

#### Day 8-10: CLI and Reporting

**New CLI Command**: `mcp-report`

**File**: `src/runtime/type_registry.py`

```python
def report_main() -> None:
    """CLI entry point for quality reporting."""
    registry = get_type_registry()
    report = registry.get_quality_report()

    print("MCP Schema Quality Report")
    print("=" * 60)
    print(f"\nTotal Tools: {report['total_tools']}")
    print("\nSchema Sources:")
    for source, count in report['by_source'].items():
        pct = count / report['total_tools'] * 100
        print(f"  {source:12} {count:3} ({pct:5.1f}%)")
    # ... more formatting ...
```

**Update**: `pyproject.toml`

```toml
[project.scripts]
mcp-generate = "runtime.generate_wrappers:main"
mcp-discover = "runtime.discover_schemas:main"
mcp-exec = "runtime.harness:main"
mcp-report = "runtime.type_registry:report_main"  # NEW
```

**Success Criteria**:
- [ ] `uv run mcp-report` works
- [ ] Shows accurate metrics
- [ ] Good formatting

---

### Phase 2: Smart Wrappers (Week 3-4)

#### Day 11-15: Three Wrapper Strategies

**File**: `src/runtime/generate_wrappers.py`

**Implement**:
```python
def generate_tool_wrapper_v2(
    server_name: str,
    tool_name: str,
    tool: Any,
    type_info: Optional[ToolTypeInfo] = None
) -> str:
    """Generate wrapper based on schema quality."""
    if tool.outputSchema:
        return _generate_typed_wrapper(...)
    elif type_info and type_info.quality == SchemaQuality.HIGH:
        return _generate_inferred_wrapper(...)
    else:
        return _generate_dict_wrapper(...)

def _generate_typed_wrapper(...) -> str:
    # Full Pydantic model, strict validation

def _generate_inferred_wrapper(...) -> str:
    # Pydantic model with warnings, Optional fields

def _generate_dict_wrapper(...) -> str:
    # Helper class with safe accessors
```

**Test Coverage**:
- Each wrapper strategy generates correct code
- Helper methods work
- Type hints correct

**Success Criteria**:
- [ ] Three strategies implemented
- [ ] Generated code is valid Python
- [ ] Helper wrapper tests pass
- [ ] Backward compatible

---

#### Day 16-18: Update Main Generation Flow

**File**: `src/runtime/generate_wrappers.py`

**Changes**:
```python
def generate_tool_wrapper(server_name: str, tool_name: str, tool: Any) -> str:
    # NEW: Get type info from registry
    registry = get_type_registry()
    tool_id = f"{server_name}__{tool.name}"
    type_info = registry.get_tool_info(tool_id)

    # NEW: Use adaptive generation
    return generate_tool_wrapper_v2(server_name, tool_name, tool, type_info)
```

**Success Criteria**:
- [ ] Wrappers adapt to schema quality
- [ ] Declared schemas → typed wrappers
- [ ] Unknown schemas → helper wrappers
- [ ] Integration tests pass

---

#### Day 19-20: Documentation and Examples

**Create**: Example wrappers for each strategy

**Update**: README.md with schema quality section

**Success Criteria**:
- [ ] Examples show all three strategies
- [ ] Documentation explains quality levels
- [ ] Migration guide complete

---

### Phase 3: Auto Evolution (Week 5-6)

#### Day 21-25: Schema Evolution Manager

**File**: `src/runtime/schema_evolution.py`

**Implement**:
```python
class SchemaEvolutionManager:
    def __init__(self, registry: TypeRegistry, output_dir: Path)

    async def check_for_improvements(self) -> list[str]:
        # Compare last_generated vs current quality

    def _should_regenerate(self, old_quality, new_quality, info) -> bool:
        # Quality threshold logic

    async def regenerate_improved_tools(self) -> int:
        # Regenerate wrappers for improved tools

    async def _regenerate_single_tool(self, info: ToolTypeInfo) -> None:
        # Generate new wrapper code

    def _generate_inferred_output_model(self, info: ToolTypeInfo) -> str:
        # Create Pydantic model from inferred fields

    def _merge_wrapper_code(self, existing, new_wrapper, output_model) -> str:
        # AST-based merging (or simple replacement)

async def evolve_schemas_background(interval_seconds: int = 300) -> None:
    # Background task
```

**Test Coverage**:
- Quality improvement detection
- Regeneration triggers
- Code merging
- Background task

**Success Criteria**:
- [ ] Detects quality improvements
- [ ] Regenerates wrappers correctly
- [ ] Preserves params models
- [ ] Background task works

---

#### Day 26-28: Integration with Harness

**File**: `src/runtime/harness.py`

**Optional Integration** (can be manual CLI instead):

```python
async def run_script_with_harness(script_path: Path) -> int:
    manager = McpClientManager()
    await manager.initialize()

    # OPTIONAL: Start background evolution
    evolution_task = None
    if ENABLE_AUTO_EVOLUTION:  # Config flag
        from .schema_evolution import evolve_schemas_background
        evolution_task = asyncio.create_task(evolve_schemas_background())

    try:
        # Run user script
        # ...
    finally:
        if evolution_task:
            evolution_task.cancel()
        await manager.cleanup()
```

**Alternative**: Manual CLI

```python
# src/runtime/schema_evolution.py

def evolve_main() -> None:
    """CLI entry point for manual evolution."""
    asyncio.run(manual_evolve())

async def manual_evolve() -> None:
    registry = get_type_registry()
    output_dir = Path(__file__).parent.parent.parent / "servers"
    manager = SchemaEvolutionManager(registry, output_dir)
    count = await manager.regenerate_improved_tools()
    print(f"Evolved {count} tool wrappers")
```

**Update**: `pyproject.toml`

```toml
[project.scripts]
mcp-evolve = "runtime.schema_evolution:evolve_main"  # NEW
```

**Success Criteria**:
- [ ] Manual evolution works: `uv run mcp-evolve`
- [ ] OR background task works (if implemented)
- [ ] Wrappers regenerate correctly
- [ ] No breaking changes

---

#### Day 29-30: Evolution Testing

**File**: `tests/integration/test_learning_workflow.py`

**Test**:
```python
async def test_unknown_to_high_quality_progression():
    # Execute tool 100+ times
    # Verify quality transitions: NONE → LOW → MEDIUM → HIGH
    # Verify wrapper regeneration
    # Verify new wrapper has better types
```

**Success Criteria**:
- [ ] Full lifecycle test passes
- [ ] Quality progression validated
- [ ] Regeneration verified

---

### Phase 4: Integrated Discovery (Week 7-8)

#### Day 31-35: Integrated Workflow

**File**: `src/runtime/generate_wrappers.py`

**Implement**:
```python
async def generate_wrappers_with_discovery(
    config_path: Path | None = None,
    discover_safe_tools: bool = True,
    discovery_config_path: Path | None = None
) -> None:
    """Generate + discover + evolve in one command."""

    # Phase 1: Generate base wrappers
    await generate_wrappers(config_path)

    if not discover_safe_tools:
        return

    # Phase 2: Check for discovery config
    discovery_file = discovery_config_path or Path.cwd() / "discovery_config.json"
    if not discovery_file.exists():
        logger.info("No discovery config - skipping")
        return

    # Phase 3: Discover schemas
    await discover_schemas(discovery_file)

    # Phase 4: Regenerate improved wrappers
    registry = get_type_registry()
    evolution = SchemaEvolutionManager(registry, output_dir)
    improved_count = await evolution.regenerate_improved_tools()

    # Phase 5: Report quality
    report = registry.get_quality_report()
    print_quality_report(report)
```

**Update CLI**:
```python
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-discover", action="store_true")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--discovery-config", type=Path)
    args = parser.parse_args()

    asyncio.run(generate_wrappers_with_discovery(
        config_path=args.config,
        discover_safe_tools=not args.no_discover,
        discovery_config_path=args.discovery_config
    ))
```

**Success Criteria**:
- [ ] `uv run mcp-generate` does everything
- [ ] `--no-discover` flag works
- [ ] Quality report shows results

---

#### Day 36-38: Documentation

**Create**: `docs/SCHEMA_GUIDE.md`

**Sections**:
1. Understanding Schema Quality
2. Three Quality Levels
3. Working with Helper Wrappers
4. Configuring Discovery
5. Monitoring Quality
6. Manual Evolution

**Update**: `README.md`

**Add**:
- Schema quality section
- Updated workflow
- New CLI commands

**Success Criteria**:
- [ ] Comprehensive guide written
- [ ] Examples included
- [ ] README updated

---

#### Day 39-40: Final Testing and Polish

**Tasks**:
- [ ] Run full test suite
- [ ] Test on real MCP servers
- [ ] Verify backward compatibility
- [ ] Performance testing
- [ ] Documentation review

---

## Code Snippets Reference

### Registry Observation Logic

```python
def observe_execution(self, tool_id: str, response: Any) -> None:
    info = self._tools.get(tool_id)
    if not info:
        return

    info.observation_count += 1
    info.last_observed = datetime.now()

    if isinstance(response, dict):
        for field, value in response.items():
            inferred_type = infer_python_type(value)

            if field in info.inferred_fields:
                # Check consistency
                if info.inferred_fields[field] == inferred_type:
                    info.field_consistency[field] += 0.1
                else:
                    info.field_consistency[field] -= 0.2
                    info.inferred_fields[field] = "Any"
            else:
                # New field
                info.inferred_fields[field] = inferred_type
                info.field_consistency[field] = 0.5

    # Update quality
    self._update_quality(info)
    self._persist()
```

### Helper Wrapper Template

```python
HELPER_WRAPPER_TEMPLATE = '''
class {model_name}Response:
    """Response wrapper with safe accessors."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def require(self, key: str) -> Any:
        if key not in self._data:
            raise KeyError(f"Required field '{key}' not found")
        return self._data[key]

    def has(self, key: str) -> bool:
        return key in self._data

    @property
    def raw(self) -> Dict[str, Any]:
        return self._data

async def {func_name}(params: {params_model}) -> {model_name}Response:
    """
    {description}

    Schema: UNKNOWN (will improve with usage)
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    result = await call_mcp_tool("{tool_id}", params.model_dump(exclude_none=True))
    unwrapped = getattr(result, "value", result)
    normalized = normalize_field_names(unwrapped, "{server_name}")

    return {model_name}Response(normalized)
'''
```

### Quality Report Formatting

```python
def print_quality_report(report: dict[str, Any]) -> None:
    print("\nMCP Schema Quality Report")
    print("=" * 60)
    print(f"\nTotal Tools: {report['total_tools']}")

    print("\nSchema Sources:")
    for source in SchemaSource:
        count = report['by_source'].get(source, 0)
        pct = count / report['total_tools'] * 100 if report['total_tools'] > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  {source.value:12} {count:3} ({pct:5.1f}%) {bar}")

    print("\nSchema Quality:")
    for quality in SchemaQuality:
        count = report['by_quality'].get(quality, 0)
        pct = count / report['total_tools'] * 100 if report['total_tools'] > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  {quality.value:12} {count:3} ({pct:5.1f}%) {bar}")

    high_pct = report['high_quality_percentage']
    print(f"\nHigh Quality Coverage: {high_pct:.1f}%")
```

---

## Testing Checklist

### Unit Tests

- [ ] Registry persistence (save/load cycle)
- [ ] Tool registration (with/without output schema)
- [ ] Observation recording
- [ ] Quality calculation
- [ ] Field consistency tracking
- [ ] Quality report generation
- [ ] Typed wrapper generation
- [ ] Inferred wrapper generation
- [ ] Helper wrapper generation
- [ ] Evolution detection logic
- [ ] Code merging (AST or simple)

### Integration Tests

- [ ] End-to-end wrapper generation
- [ ] Discovery integration
- [ ] Evolution after observations
- [ ] Full lifecycle (unknown → high quality)
- [ ] Backward compatibility
- [ ] Multiple servers

### Performance Tests

- [ ] Registry operations don't slow execution
- [ ] Persistence is fast (< 10ms)
- [ ] Background evolution doesn't block
- [ ] Memory usage acceptable

---

## Common Issues and Solutions

### Issue: Registry file corrupted

**Solution**: Implement atomic writes
```python
def _persist(self) -> None:
    temp_file = self._storage / "type_registry.json.tmp"
    final_file = self._storage / "type_registry.json"

    with open(temp_file, "w") as f:
        json.dump(data, f, indent=2, default=str)

    temp_file.rename(final_file)  # Atomic on POSIX
```

### Issue: Evolution breaks wrapper

**Solution**: Never change function signature
```python
# WRONG - changes signature
async def tool(params) -> NewType:  # Breaks existing code

# RIGHT - maintains signature, improves internals
async def tool(params) -> ToolResult:  # Same signature
    # Better model inside, but compatible
```

### Issue: False high quality

**Solution**: Require consistency
```python
def _update_quality(self, info: ToolTypeInfo) -> None:
    if info.observation_count >= 100:
        # Check consistency
        avg_consistency = mean(info.field_consistency.values())
        if avg_consistency >= 0.8:
            info.quality = SchemaQuality.HIGH
        else:
            info.quality = SchemaQuality.MEDIUM
```

---

## Performance Targets

| Operation | Target | Acceptable |
|-----------|--------|-----------|
| Registry load | < 5ms | < 20ms |
| Registry save | < 10ms | < 50ms |
| Observe execution | < 1ms | < 5ms |
| Quality check | < 1ms | < 5ms |
| Wrapper regeneration | < 100ms/tool | < 500ms/tool |
| Background evolution | < 1s total | < 5s total |

---

## Rollback Plan

If implementation fails:

1. **Phase 1 Rollback**:
   - Remove type_registry.py
   - Revert changes to generate_wrappers.py
   - Revert changes to mcp_client.py
   - Delete .mcp_runtime/ directory

2. **Phase 2 Rollback**:
   - Revert wrapper generation changes
   - Regenerate wrappers with old logic

3. **Phase 3 Rollback**:
   - Remove schema_evolution.py
   - Remove background task from harness

4. **Phase 4 Rollback**:
   - Revert generate_wrappers_with_discovery
   - Keep separate discovery command

All rollbacks should maintain backward compatibility.

---

## Success Metrics

After 6 months of production use:

| Metric | Target |
|--------|--------|
| High quality schema coverage | > 85% |
| Defensive code reduction | > 70% |
| Developer satisfaction | Positive |
| Bug reports related to schemas | < 5 |
| Performance regression | None |

---

**End of Implementation Reference**

This guide provides the essential information needed to implement the output schema solution. Refer to the full architecture document for detailed rationale and design decisions.
