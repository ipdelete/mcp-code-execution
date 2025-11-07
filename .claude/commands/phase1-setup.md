---
description: Phase 1 - Project Setup & Structure
model: sonnet
---

# Phase 1: Project Setup & Structure

**Goal**: Set up complete Python project with modern tooling (uv + src/ layout)

**Tasks**: T012-T028 | **Validation**: CHK016-CHK022, CHK104-CHK111

## Context: Read plan.md First

Review `plan.md` section: **Phase 1: Project Setup & Structure (lines 148-304)** for comprehensive architecture and configuration details.

## Prerequisites

- ✅ Phase 0 PoC completed with GO decision
- ✅ uv installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Instructions

### 1. Preserve TypeScript Reference (T012-T013)

```bash
# Create reference directory
mkdir -p _typescript_reference

# Move TypeScript files for reference
git mv runtime _typescript_reference/runtime
git mv tests/*.ts _typescript_reference/tests/ 2>/dev/null || true

# Commit
git add -A
git commit -m "chore: Move TypeScript files to reference folder during Python port"
```

### 2. Initialize Python Project (T014-T015)

```bash
# Initialize uv project
uv init --lib --name mcp-execution

# Pin Python version
uv python pin 3.11

# Verify .python-version created
cat .python-version
```

### 3. Create pyproject.toml (T016-T020)

Create `pyproject.toml` with complete configuration:

```toml
[project]
name = "mcp-execution"
version = "0.1.0"
description = "Progressive tool discovery pattern for MCP (98.7% token reduction)"
requires-python = ">=3.11"
readme = "README.md"
license = { text = "MIT" }

dependencies = [
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
    "aiofiles>=23.0.0",
]

[project.optional-dependencies]
dev = [
    "black>=24.0.0",
    "mypy>=1.8.0",
    "ruff>=0.2.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[project.scripts]
mcp-exec = "runtime.harness:main"
mcp-generate = "runtime.generate_wrappers:main"
mcp-discover = "runtime.discover_schemas:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.mypy]
strict = true
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.ruff]
line-length = 100
target-version = "py311"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

### 4. Update .gitignore (T021)

Add Python-specific entries to `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.mypy_cache/
.ruff_cache/
*.egg-info/
dist/
build/
.uv/

# Generated servers (keep this)
servers/
src/servers/

# Virtual environments
.venv/
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.coverage
htmlcov/

# Temporary files
*.log
*.tmp
poc_*.py
poc_findings.md
```

### 5. Create Directory Structure (T022-T023)

```bash
# Create package directories
mkdir -p src/runtime
mkdir -p src/servers
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p workspace

# Create package markers
touch src/__init__.py
touch src/runtime/__init__.py
touch src/servers/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

# Verify structure
tree -L 3 src/ tests/ workspace/
```

### 6. Create Error Handling Infrastructure (T024)

Create `src/runtime/exceptions.py`:

```python
"""Custom exceptions for MCP execution runtime."""


class McpExecutionError(Exception):
    """Base exception for MCP execution errors."""

    pass


class ServerConnectionError(McpExecutionError):
    """Failed to connect to MCP server."""

    pass


class ToolNotFoundError(McpExecutionError):
    """Tool not found on any configured server."""

    def __init__(self, tool_identifier: str) -> None:
        super().__init__(f"Tool not found: {tool_identifier}")
        self.tool_identifier = tool_identifier


class ToolExecutionError(McpExecutionError):
    """Tool execution failed."""

    def __init__(self, tool_identifier: str, message: str) -> None:
        super().__init__(f"Tool execution failed for {tool_identifier}: {message}")
        self.tool_identifier = tool_identifier


class ConfigurationError(McpExecutionError):
    """Invalid configuration."""

    pass


class SchemaValidationError(McpExecutionError):
    """Schema validation failed."""

    pass
```

### 7. Create Config Validation (T025)

Create `src/runtime/config.py`:

```python
"""Configuration models for MCP servers."""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    command: str
    args: list[str]
    env: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic configuration."""

        extra = "forbid"  # Fail on unknown fields


class McpConfig(BaseModel):
    """Root configuration for all MCP servers."""

    mcpServers: Dict[str, ServerConfig] = Field(alias="mcpServers")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True
        extra = "forbid"
```

### 8. Install Dependencies (T026-T027)

```bash
# Generate lock file and install all dependencies
uv sync --all-extras

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Verify installation
uv pip list | grep -E "(mcp|pydantic|aiofiles|black|mypy|ruff|pytest)"
```

### 9. Validate Setup (T028)

```bash
# Verify directory structure
ls -la src/runtime/
ls -la src/servers/
ls -la tests/

# Verify files exist
test -f src/runtime/exceptions.py && echo "✅ exceptions.py exists"
test -f src/runtime/config.py && echo "✅ config.py exists"
test -f pyproject.toml && echo "✅ pyproject.toml exists"
test -f .python-version && echo "✅ .python-version exists"

# Test imports
python -c "from runtime.exceptions import McpExecutionError; print('✅ Exceptions import works')"
python -c "from runtime.config import McpConfig; print('✅ Config import works')"

# Verify tools work
uv run black --version
uv run mypy --version
uv run ruff --version
uv run pytest --version
```

## Validation Checklist

- [ ] CHK016 - pyproject.toml includes all required dependencies?
- [ ] CHK017 - Dev dependencies complete?
- [ ] CHK018 - .gitignore configured for Python + servers/?
- [ ] CHK019 - exceptions.py covers all error scenarios?
- [ ] CHK020 - config.py uses Pydantic validation?
- [ ] CHK021 - TypeScript reference strategy documented?
- [ ] CHK022 - All directory structures created?
- [ ] CHK104 - mcp>=1.0.0 dependency appropriate?
- [ ] CHK105 - pydantic>=2.0.0 dependency appropriate?
- [ ] CHK106 - All dev dependencies listed?
- [ ] CHK107 - pyproject.toml compatible with uv?
- [ ] CHK108 - .python-version set to 3.11+?
- [ ] CHK109 - black line-length = 100?
- [ ] CHK110 - mypy strict = true?
- [ ] CHK111 - ruff targets Python 3.11?

## Deliverables

- ✅ TypeScript files in `_typescript_reference/`
- ✅ `pyproject.toml` with uv configuration
- ✅ `.python-version` (3.11)
- ✅ Updated `.gitignore`
- ✅ `src/` structure with packages
- ✅ `src/runtime/exceptions.py`
- ✅ `src/runtime/config.py`
- ✅ `uv.lock` generated
- ✅ Dependencies installed

## Troubleshooting

**Issue**: `uv` command not found
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or ~/.zshrc
```

**Issue**: Python 3.11 not available
```bash
uv python install 3.11
```

**Issue**: Import errors
```bash
# Ensure src/ is in PYTHONPATH or use editable install
uv pip install -e .
```

## Mark Items Complete

After successfully completing this phase, mark the following as complete:

### Update CHECKLIST.md (CHK016-CHK022, CHK104-CHK111)
```bash
# Mark Phase 1 checklist items complete
for i in {016..022}; do
  sed -i '' "s/^- \[ \] CHK$i/- [x] CHK$i/" CHECKLIST.md
done

for i in {104..111}; do
  sed -i '' "s/^- \[ \] CHK$i/- [x] CHK$i/" CHECKLIST.md
done

echo "✅ Phase 1 checklist items marked complete"
```

### Update TASKS.md (T012-T028)
```bash
# Mark Phase 1 task items complete
for i in {012..028}; do
  sed -i '' "s/^- \[ \] T$i/- [x] T$i/" TASKS.md
done

echo "✅ Phase 1 task items marked complete"
```

### Verify Completion
```bash
# Verify all Phase 1 items marked
grep "CHK0[12][0-9]" CHECKLIST.md | grep "\[x\]" | wc -l  # Should be 15 (7 + 8)
grep "T0[12][0-9]" TASKS.md | grep "\[x\]" | wc -l  # Should be 17

echo "✅ Phase 1 complete and documented"
```

---

**Next Phase**: Proceed to `/phase2-client` to implement MCP Client Manager
