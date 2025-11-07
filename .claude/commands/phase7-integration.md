---
description: Phase 7 - Integration Testing & Example
model: sonnet
---

# Phase 7: Integration Testing & Example Script

**Goal**: Validate end-to-end functionality with real MCP servers

**Tasks**: T117-T129 | **Validation**: CHK072-CHK078, CHK101-CHK103

## Prerequisites

- ✅ Phase 2 completed (MCP Client Manager)
- ✅ Phase 3 completed (Harness)
- ✅ Phase 5 completed (Wrapper Generation)
- ✅ `mcp_config.json` exists with git and fetch servers

## Context

This phase validates the **98.7% token reduction pattern** end-to-end:
1. Agent explores `./servers/` to discover tools
2. Agent reads only needed tool definitions
3. Agent writes script that processes data locally
4. Script returns summary only (not raw data)

## Instructions

### 1. Verify mcp_config.json (T117)

Ensure `mcp_config.json` exists at project root:

```json
{
  "mcpServers": {
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"]
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    }
  }
}
```

### 2. Create Git Server Integration Tests (T118-T119)

Create `tests/integration/test_git_server.py`:

```python
"""Integration tests with real git MCP server."""

import pytest
from pathlib import Path

from runtime.mcp_client import get_mcp_client_manager
from runtime.exceptions import ToolNotFoundError


@pytest.mark.asyncio
async def test_git_server_connection():
    """Test that git server can be connected."""
    manager = get_mcp_client_manager()
    config_path = Path.cwd() / "mcp_config.json"

    await manager.initialize(config_path)

    # Verify git server is in config
    assert "git" in manager._config.mcpServers


@pytest.mark.asyncio
async def test_git_status_tool():
    """Test calling git_status tool."""
    manager = get_mcp_client_manager()
    config_path = Path.cwd() / "mcp_config.json"

    await manager.initialize(config_path)

    # Call git_status on current repo
    result = await manager.call_tool("git__git_status", {"repo_path": "."})

    assert result is not None
    # Result should contain git status info
    # (structure varies, but should be dict or string)
    assert isinstance(result, (dict, str, list))


@pytest.mark.asyncio
async def test_git_log_tool():
    """Test calling git_log tool."""
    manager = get_mcp_client_manager()
    config_path = Path.cwd() / "mcp_config.json"

    await manager.initialize(config_path)

    # Call git_log with limit
    result = await manager.call_tool(
        "git__git_log", {"repo_path": ".", "max_count": 5}
    )

    assert result is not None


@pytest.mark.asyncio
async def test_tool_not_found():
    """Test that calling non-existent tool raises error."""
    manager = get_mcp_client_manager()
    config_path = Path.cwd() / "mcp_config.json"

    await manager.initialize(config_path)

    with pytest.raises(ToolNotFoundError):
        await manager.call_tool("git__nonexistent_tool", {})


@pytest.mark.asyncio
async def test_server_not_found():
    """Test that calling tool on non-existent server raises error."""
    manager = get_mcp_client_manager()
    config_path = Path.cwd() / "mcp_config.json"

    await manager.initialize(config_path)

    with pytest.raises(ToolNotFoundError):
        await manager.call_tool("nonexistent__tool", {})


@pytest.mark.asyncio
async def test_lazy_connection():
    """Test that server connects lazily on first tool call."""
    manager = get_mcp_client_manager()
    config_path = Path.cwd() / "mcp_config.json"

    await manager.initialize(config_path)

    # After initialize, no connections should exist
    assert len(manager._clients) == 0

    # Call tool
    await manager.call_tool("git__git_status", {"repo_path": "."})

    # Now git server should be connected
    assert "git" in manager._clients


@pytest.mark.asyncio
async def test_cleanup():
    """Test that cleanup closes all connections."""
    manager = get_mcp_client_manager()
    config_path = Path.cwd() / "mcp_config.json"

    await manager.initialize(config_path)
    await manager.call_tool("git__git_status", {"repo_path": "."})

    # Verify connection exists
    assert len(manager._clients) > 0

    # Cleanup
    await manager.cleanup()

    # Verify connections closed
    assert len(manager._clients) == 0
    assert manager._initialized is False
```

### 3. Create Fetch Server Integration Tests (T120-T121)

Create `tests/integration/test_fetch_server.py`:

```python
"""Integration tests with real fetch MCP server."""

import pytest
from pathlib import Path

from runtime.mcp_client import get_mcp_client_manager


@pytest.mark.asyncio
async def test_fetch_server_connection():
    """Test that fetch server can be connected."""
    manager = get_mcp_client_manager()
    config_path = Path.cwd() / "mcp_config.json"

    await manager.initialize(config_path)

    # Verify fetch server is in config
    assert "fetch" in manager._config.mcpServers


@pytest.mark.asyncio
async def test_fetch_url():
    """Test calling fetch tool."""
    manager = get_mcp_client_manager()
    config_path = Path.cwd() / "mcp_config.json"

    await manager.initialize(config_path)

    # Fetch example.com
    result = await manager.call_tool("fetch__fetch", {"url": "https://example.com"})

    assert result is not None
    # Result should contain HTML content or error
    # Structure varies, but should have content
    assert isinstance(result, (dict, str))


@pytest.mark.asyncio
async def test_fetch_multiple_urls():
    """Test fetching multiple URLs sequentially."""
    manager = get_mcp_client_manager()
    config_path = Path.cwd() / "mcp_config.json"

    await manager.initialize(config_path)

    urls = ["https://example.com", "https://example.org"]
    results = []

    for url in urls:
        result = await manager.call_tool("fetch__fetch", {"url": url})
        results.append(result)

    # Verify both fetches succeeded
    assert len(results) == 2
    assert all(r is not None for r in results)
```

### 4. Create Harness Integration Tests (T122)

Create `tests/integration/test_harness_integration.py`:

```python
"""Integration tests for script harness."""

import pytest
import subprocess
import sys
from pathlib import Path


def test_harness_simple_script():
    """Test harness executes simple script successfully."""
    # Create test script
    test_script = Path("workspace/test_harness_simple.py")
    test_script.parent.mkdir(exist_ok=True)
    test_script.write_text(
        """
print("Test output")
"""
    )

    # Run harness
    result = subprocess.run(
        [sys.executable, "-m", "runtime.harness", str(test_script)],
        capture_output=True,
        text=True,
    )

    # Verify success
    assert result.returncode == 0
    assert "Test output" in result.stdout


def test_harness_script_with_mcp():
    """Test harness executes script that uses MCP tools."""
    # Create test script
    test_script = Path("workspace/test_harness_mcp.py")
    test_script.write_text(
        """
import asyncio
from runtime.mcp_client import call_mcp_tool

async def main():
    result = await call_mcp_tool("git__git_status", {"repo_path": "."})
    print(f"Git status result: {result is not None}")

asyncio.run(main())
"""
    )

    # Run harness
    result = subprocess.run(
        [sys.executable, "-m", "runtime.harness", str(test_script)],
        capture_output=True,
        text=True,
    )

    # Verify success
    assert result.returncode == 0
    assert "Git status result: True" in result.stdout


def test_harness_script_error():
    """Test harness handles script errors."""
    # Create failing script
    test_script = Path("workspace/test_harness_error.py")
    test_script.write_text(
        """
raise Exception("Test error")
"""
    )

    # Run harness
    result = subprocess.run(
        [sys.executable, "-m", "runtime.harness", str(test_script)],
        capture_output=True,
        text=True,
    )

    # Verify error handling
    assert result.returncode == 1
    assert "Test error" in result.stderr or "Test error" in result.stdout


def test_harness_script_not_found():
    """Test harness handles missing script."""
    # Run harness with non-existent script
    result = subprocess.run(
        [sys.executable, "-m", "runtime.harness", "workspace/nonexistent.py"],
        capture_output=True,
        text=True,
    )

    # Verify error
    assert result.returncode == 1
    assert "not found" in result.stderr.lower()
```

### 5. Create Progressive Disclosure Example (T123-T126)

Create `workspace/example_progressive_disclosure.py`:

```python
"""
Example: Progressive Disclosure Pattern

Demonstrates the 98.7% token reduction pattern:
1. Agent explores ./servers/ to discover available tools
2. Agent reads only needed tool definitions
3. Agent writes and executes this script
4. Script processes data locally
5. Only summary returned to agent

This example:
- Lists recent git commits
- Counts commits by author
- Returns summary statistics (NOT full commit data)
"""

import asyncio
from collections import Counter
from runtime.mcp_client import call_mcp_tool


async def main():
    """Analyze git commit history and return summary."""

    print("🔍 Analyzing git commit history...")

    # Get recent commits (progressive disclosure: fetch data once)
    commits_result = await call_mcp_tool(
        "git__git_log",
        {
            "repo_path": ".",
            "max_count": 50,  # Limit to recent commits
        },
    )

    # Process data locally (agent doesn't see raw commits)
    print("📊 Processing commits locally...")

    # Parse commit data (structure varies by server)
    if isinstance(commits_result, str):
        # Parse text format
        commit_lines = [
            line for line in commits_result.split("\n") if line.strip()
        ]
        total_commits = len([l for l in commit_lines if l.startswith("commit")])
        authors = []
        for line in commit_lines:
            if line.startswith("Author:"):
                author = line.split("Author:")[1].strip()
                authors.append(author)
    elif isinstance(commits_result, list):
        # Parse list format
        total_commits = len(commits_result)
        authors = [
            commit.get("author", "Unknown")
            for commit in commits_result
            if isinstance(commit, dict)
        ]
    else:
        total_commits = 1
        authors = ["Unknown"]

    # Calculate statistics
    author_counts = Counter(authors)
    unique_authors = len(author_counts)
    top_author = author_counts.most_common(1)[0] if author_counts else ("None", 0)

    # Return SUMMARY only (not raw data)
    summary = {
        "total_commits_analyzed": total_commits,
        "unique_authors": unique_authors,
        "top_contributor": {
            "name": top_author[0],
            "commits": top_author[1],
        },
        "authors_list": list(author_counts.keys())[:5],  # Top 5 only
    }

    print("\n✅ Analysis complete!")
    print("\n📈 Summary:")
    print(f"  Total commits analyzed: {summary['total_commits_analyzed']}")
    print(f"  Unique authors: {summary['unique_authors']}")
    print(f"  Top contributor: {summary['top_contributor']['name']} "
          f"({summary['top_contributor']['commits']} commits)")

    return summary


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n📤 Summary output: {result}")
```

### 6. Test Example Execution (T127-T128)

```bash
# Execute example script
uv run python -m runtime.harness workspace/example_progressive_disclosure.py

# Expected output:
# [INFO] Script: .../workspace/example_progressive_disclosure.py
# [INFO] MCP client manager initialized
# [INFO] Executing script: ...
# 🔍 Analyzing git commit history...
# 📊 Processing commits locally...
# ✅ Analysis complete!
# 📈 Summary:
#   Total commits analyzed: 50
#   Unique authors: 3
#   Top contributor: John Doe (30 commits)
# 📤 Summary output: {...}
# [INFO] Script execution completed
# [INFO] Cleanup complete

# Verify pattern:
# 1. ✅ Script fetched data once (git_log)
# 2. ✅ Processed data locally (Counter, analysis)
# 3. ✅ Returned summary only (not 50 full commits)
# 4. ✅ Token reduction: ~98% (summary vs full commits)
```

### 7. Run All Integration Tests (T129)

```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run with output
uv run pytest tests/integration/ -v -s

# Run specific test file
uv run pytest tests/integration/test_git_server.py -v

# Expected: All tests passing
```

## Validation Checklist

- [ ] CHK072 - Integration tests for git server (git_status)?
- [ ] CHK073 - Integration tests for fetch server (fetch_url)?
- [ ] CHK074 - Example demonstrates 98.7% token reduction?
- [ ] CHK075 - Example processes data locally and returns summaries?
- [ ] CHK076 - Example executable via harness?
- [ ] CHK077 - Example uses call_mcp_tool or generated wrappers?
- [ ] CHK078 - End-to-end functionality verified with real servers?
- [ ] CHK101 - Integration tests for filesystem server? (optional)
- [ ] CHK102 - Integration tests for github server? (optional)
- [ ] CHK103 - Integration tests for harness?

## Deliverables

- ✅ `tests/integration/test_git_server.py` with integration tests
- ✅ `tests/integration/test_fetch_server.py` with integration tests
- ✅ `tests/integration/test_harness_integration.py` with harness tests
- ✅ `workspace/example_progressive_disclosure.py` demonstrating pattern
- ✅ All integration tests passing
- ✅ End-to-end validation complete

## Token Reduction Validation

### Before (Traditional Approach)
```
Agent Request: "Analyze git commits by author"
Response: [50 full commit objects with all fields] = ~50KB
Agent processes ~50KB of data
```

### After (Progressive Disclosure)
```
Agent Request: "Analyze git commits by author"
Agent: Writes script that fetches and processes locally
Response: {summary: {total: 50, authors: 3, top: "John"}} = ~100 bytes
Agent processes ~100 bytes of data
```

**Token Reduction**: ~99.8% (100 bytes / 50KB)

## Testing Different Scenarios

### Scenario 1: Multiple Tool Calls
Create `workspace/test_multiple_tools.py`:

```python
import asyncio
from runtime.mcp_client import call_mcp_tool

async def main():
    # Call multiple tools
    status = await call_mcp_tool("git__git_status", {"repo_path": "."})
    log = await call_mcp_tool("git__git_log", {"repo_path": ".", "max_count": 5})

    print(f"Status: {status is not None}")
    print(f"Log: {log is not None}")

asyncio.run(main())
```

### Scenario 2: Error Handling
Create `workspace/test_error_handling.py`:

```python
import asyncio
from runtime.mcp_client import call_mcp_tool
from runtime.exceptions import ToolNotFoundError

async def main():
    try:
        await call_mcp_tool("git__nonexistent", {})
    except ToolNotFoundError as e:
        print(f"✅ Caught expected error: {e}")

asyncio.run(main())
```

## Troubleshooting

**Issue**: Integration tests fail with connection errors
```bash
# Verify npx is installed
npx --version

# Verify MCP servers can be installed
npx -y @modelcontextprotocol/server-git --help
npx -y @modelcontextprotocol/server-fetch --help
```

**Issue**: Tests fail with import errors
```bash
# Ensure editable install
uv pip install -e .

# Verify imports work
python -c "from runtime.mcp_client import call_mcp_tool; print('✅')"
```

**Issue**: Example script doesn't demonstrate pattern
```python
# Verify:
# 1. Script fetches data (tool calls)
# 2. Script processes locally (Python code)
# 3. Script returns summary (print/return)
# 4. Summary is much smaller than raw data
```

## Mark Items Complete

After successfully completing this phase, mark the following as complete:

### Update CHECKLIST.md (CHK072-CHK078, CHK101-CHK103)
```bash
# Mark Phase 7 checklist items complete
for i in {072..078}; do
  sed -i '' "s/^- \[ \] CHK$i/- [x] CHK$i/" CHECKLIST.md
done

for i in {101..103}; do
  sed -i '' "s/^- \[ \] CHK$i/- [x] CHK$i/" CHECKLIST.md
done

echo "✅ Phase 7 checklist items marked complete"
```

### Update TASKS.md (T117-T129)
```bash
# Mark Phase 7 task items complete
for i in {117..129}; do
  sed -i '' "s/^- \[ \] T$i/- [x] T$i/" TASKS.md
done

echo "✅ Phase 7 task items marked complete"
```

### Verify Completion
```bash
echo "✅ Phase 7 complete and documented"
```

---

**Next Phase**: Proceed to `/phase8-docs` to complete documentation
