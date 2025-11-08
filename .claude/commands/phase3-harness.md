---
description: Phase 3 - Script Execution Harness
model: sonnet
---

# Phase 3: Script Execution Harness

**Goal**: CLI entry point for executing Python scripts with MCP support

**Tasks**: T050-T064 | **Validation**: CHK033-CHK041, CHK117-CHK118

## Context: Read plan.md First

Review `plan.md` section: **Phase 3: Script Execution Harness (lines 417-535)** for detailed harness design and signal handling patterns.

## Prerequisites

- ✅ Phase 2 completed (MCP Client Manager)
- ✅ TypeScript reference at `_typescript_reference/runtime/harness.ts`

## Key Features

1. CLI argument parsing (script path)
2. Signal handlers (SIGINT/SIGTERM) - **ASYNC-SAFE APPROACH**
3. Script execution with `runpy` (isolated namespace)
4. Proper cleanup with error handling
5. Standard exit codes (0=success, 1=error, 130=Ctrl+C)

## Instructions

### 1. Create Harness Skeleton (T050-T051)

Create `src/runtime/harness.py`:

```python
"""
Script execution harness for MCP-enabled Python scripts.

This harness:
1. Initializes MCP client manager
2. Executes user script with MCP tools available
3. Handles signals gracefully (SIGINT/SIGTERM)
4. Cleans up all connections on exit
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import NoReturn

from .mcp_client import get_mcp_client_manager
from .exceptions import McpExecutionError

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger("mcp_execution.harness")


async def main() -> NoReturn:
    """Main entry point for script execution."""
    # Implementation in next steps
    pass


if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Implement CLI Argument Parsing (T051-T052)

Add to `main()`:

```python
async def main() -> NoReturn:
    """Main entry point for script execution."""
    # 1. Parse CLI arguments
    if len(sys.argv) < 2:
        logger.error("Usage: python -m runtime.harness <script_path>")
        sys.exit(1)

    script_path = Path(sys.argv[1]).resolve()

    # 2. Validate script exists
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        sys.exit(1)

    if not script_path.is_file():
        logger.error(f"Not a file: {script_path}")
        sys.exit(1)

    logger.info(f"Script: {script_path}")
```

### 3. Implement sys.path Management (T053)

Add after validation:

```python
    # 3. Add src/ to Python path for imports
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        logger.debug(f"Added to sys.path: {src_path}")
```

### 4. Initialize MCP Client Manager (T054)

Add after sys.path management:

```python
    # 4. Initialize MCP client manager
    manager = get_mcp_client_manager()
    try:
        await manager.initialize()
        logger.info("MCP client manager initialized")
    except McpExecutionError as e:
        logger.error(f"Failed to initialize MCP client: {e}")
        sys.exit(1)
```

### 5. Implement Signal Handlers (T055) - **CRITICAL: ASYNC-SAFE**

Add after manager initialization:

```python
    # 5. Set up signal handling (CORRECT async approach)
    shutdown_event = asyncio.Event()

    def signal_handler(signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, shutting down...")
        shutdown_event.set()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
```

### 6. Implement Script Execution (T056-T058)

Add execution logic:

```python
    # 6. Execute the script using runpy
    exit_code = 0
    try:
        # Check if shutdown was requested before execution
        if shutdown_event.is_set():
            logger.info("Shutdown requested before execution")
            sys.exit(130)

        # Execute script in isolated namespace
        logger.info(f"Executing script: {script_path}")
        import runpy
        runpy.run_path(str(script_path), run_name="__main__")

        logger.info("Script execution completed")

    except KeyboardInterrupt:
        logger.info("Execution interrupted by user")
        exit_code = 130  # Standard exit code for Ctrl+C

    except Exception as e:
        logger.error(f"Script execution failed: {e}", exc_info=True)
        exit_code = 1

    finally:
        # 7. Cleanup
        logger.debug("Cleaning up MCP connections...")
        try:
            await manager.cleanup()
            logger.info("Cleanup complete")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
            if exit_code == 0:
                exit_code = 1

        sys.exit(exit_code)
```

### 7. Complete Implementation (T059-T061)

Full `src/runtime/harness.py`:

```python
"""
Script execution harness for MCP-enabled Python scripts.

This harness:
1. Initializes MCP client manager
2. Executes user script with MCP tools available
3. Handles signals gracefully (SIGINT/SIGTERM)
4. Cleans up all connections on exit
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Any, NoReturn

from .exceptions import McpExecutionError
from .mcp_client import get_mcp_client_manager

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] %(message)s", stream=sys.stderr
)

logger = logging.getLogger("mcp_execution.harness")


async def main() -> NoReturn:
    """Main entry point for script execution."""

    # 1. Parse CLI arguments
    if len(sys.argv) < 2:
        logger.error("Usage: python -m runtime.harness <script_path>")
        sys.exit(1)

    script_path = Path(sys.argv[1]).resolve()

    # 2. Validate script exists
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        sys.exit(1)

    if not script_path.is_file():
        logger.error(f"Not a file: {script_path}")
        sys.exit(1)

    logger.info(f"Script: {script_path}")

    # 3. Add src/ to Python path for imports
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        logger.debug(f"Added to sys.path: {src_path}")

    # 4. Initialize MCP client manager
    manager = get_mcp_client_manager()
    try:
        await manager.initialize()
        logger.info("MCP client manager initialized")
    except McpExecutionError as e:
        logger.error(f"Failed to initialize MCP client: {e}")
        sys.exit(1)

    # 5. Set up signal handling (CORRECT async approach)
    shutdown_event = asyncio.Event()

    def signal_handler(signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, shutting down...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 6. Execute the script using runpy
    exit_code = 0
    try:
        # Check if shutdown was requested
        if shutdown_event.is_set():
            logger.info("Shutdown requested before execution")
            sys.exit(130)

        # Execute script in isolated namespace
        logger.info(f"Executing script: {script_path}")
        import runpy

        runpy.run_path(str(script_path), run_name="__main__")

        logger.info("Script execution completed")

    except KeyboardInterrupt:
        logger.info("Execution interrupted by user")
        exit_code = 130  # Standard exit code for Ctrl+C

    except Exception as e:
        logger.error(f"Script execution failed: {e}", exc_info=True)
        exit_code = 1

    finally:
        # 7. Cleanup
        logger.debug("Cleaning up MCP connections...")
        try:
            await manager.cleanup()
            logger.info("Cleanup complete")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
            if exit_code == 0:
                exit_code = 1

        sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
```

### 8. Create Test Script (T062)

Create `workspace/test_simple.py`:

```python
"""Simple test script for harness validation."""

print("✅ Script started")
print("✅ Script completed successfully")
```

Test execution:

```bash
# Test basic execution
uv run python -m runtime.harness workspace/test_simple.py

# Expected output:
# [INFO] Script: /path/to/workspace/test_simple.py
# [INFO] MCP client manager initialized
# [INFO] Executing script: /path/to/workspace/test_simple.py
# ✅ Script started
# ✅ Script completed successfully
# [INFO] Script execution completed
# [INFO] Cleanup complete
```

### 9. Add Script Alias (T063)

Verify in `pyproject.toml` (should already be there from Phase 1):

```toml
[project.scripts]
mcp-exec = "runtime.harness:main"
```

Test alias:

```bash
# After uv sync, this should work:
uv run mcp-exec workspace/test_simple.py
```

### 10. Test Ctrl+C Handling (T064)

Create `workspace/test_long_running.py`:

```python
"""Test script for signal handling."""
import time

print("Started long-running script")
print("Press Ctrl+C to interrupt...")

for i in range(10):
    print(f"Iteration {i+1}/10")
    time.sleep(1)

print("Completed normally")
```

Test signal handling:

```bash
# Start script and press Ctrl+C after a few seconds
uv run python -m runtime.harness workspace/test_long_running.py

# Press Ctrl+C

# Expected:
# [INFO] Received SIGINT, shutting down...
# [INFO] Execution interrupted by user
# [INFO] Cleanup complete

# Check exit code:
echo $?  # Should be 130
```

## Validation Checklist

- [ ] CHK033 - Harness accepts script path as CLI argument?
- [ ] CHK034 - Script path validation implemented?
- [ ] CHK035 - Harness adds src/ to sys.path?
- [ ] CHK036 - Signal handlers use asyncio.Event (not async/await)?
- [ ] CHK037 - Harness uses runpy.run_path for execution?
- [ ] CHK038 - Logging configured to stderr with [LEVEL] format?
- [ ] CHK039 - Standard exit codes used (0, 1, 130)?
- [ ] CHK040 - Cleanup guaranteed via try/finally?
- [ ] CHK041 - Harness invokable as module and script alias?
- [ ] CHK117 - All exceptions caught and logged?
- [ ] CHK118 - Cleanup executes even if script raises?

## Deliverables

- ✅ `src/runtime/harness.py` with complete implementation
- ✅ Invokable as `uv run python -m runtime.harness script.py`
- ✅ Script alias `mcp-exec` in pyproject.toml
- ✅ Test scripts validate execution and signal handling

## Testing Scenarios

### Test 1: Successful Execution
```bash
uv run python -m runtime.harness workspace/test_simple.py
echo $?  # Should be 0
```

### Test 2: Script Not Found
```bash
uv run python -m runtime.harness workspace/nonexistent.py
echo $?  # Should be 1
```

### Test 3: Script Error
Create `workspace/test_error.py`:
```python
raise Exception("Test error")
```

```bash
uv run python -m runtime.harness workspace/test_error.py
echo $?  # Should be 1
```

### Test 4: Ctrl+C Interrupt
```bash
uv run python -m runtime.harness workspace/test_long_running.py
# Press Ctrl+C
echo $?  # Should be 130
```

## Troubleshooting

**Issue**: Import errors in executed script
```python
# Solution: Harness adds src/ to sys.path
# Scripts can import runtime modules directly
from runtime.mcp_client import call_mcp_tool
```

**Issue**: Signal handlers not working
```python
# Ensure using asyncio.Event, not async/await
shutdown_event = asyncio.Event()
def signal_handler(signum, frame):
    shutdown_event.set()  # Sync operation
```

**Issue**: Cleanup not executing
```python
# Ensure try/finally block structure
try:
    # execution
finally:
    # cleanup always runs
```

## Mark Items Complete

After successfully completing this phase, mark the following as complete:

### Update CHECKLIST.md (CHK033-CHK041, CHK117-CHK118)
```bash
# Mark Phase 3 checklist items complete
for i in {033..041}; do
  sed -i '' "s/^- \[ \] CHK$i/- [x] CHK$i/" CHECKLIST.md
done

for i in {117..118}; do
  sed -i '' "s/^- \[ \] CHK$i/- [x] CHK$i/" CHECKLIST.md
done

echo "✅ Phase 3 checklist items marked complete"
```

### Update TASKS.md (T050-T064)
```bash
# Mark Phase 3 task items complete
for i in {050..064}; do
  sed -i '' "s/^- \[ \] T$i/- [x] T$i/" TASKS.md
done

echo "✅ Phase 3 task items marked complete"
```

### Verify Completion
```bash
echo "✅ Phase 3 complete and documented"
```

---

**Next Phase**: Proceed to `/phase4-normalize` to implement field normalization
