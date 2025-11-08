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
import runpy
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


def main() -> NoReturn:
    """Entry point for the harness."""
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

    # 3. Add project root and src/ to Python path for imports
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        logger.debug(f"Added to sys.path: {src_path}")

    project_root = src_path.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.debug(f"Added to sys.path: {project_root}")

    # 4. Create a persistent event loop to be used throughout the harness
    # This ensures async context managers are entered and exited in the same loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 5. Initialize MCP client manager
    manager = get_mcp_client_manager()
    try:
        loop.run_until_complete(manager.initialize())
        logger.info("MCP client manager initialized")
    except McpExecutionError as e:
        logger.error(f"Failed to initialize MCP client: {e}")
        sys.exit(1)

    # 6. Set up signal handling for the script execution
    def signal_handler(signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, shutting down...")
        sys.exit(130)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 7. Execute the script (synchronously, no nested event loop)
    exit_code = 0
    try:
        logger.info(f"Executing script: {script_path}")
        runpy.run_path(str(script_path), run_name="__main__")
        logger.info("Script execution completed")

    except KeyboardInterrupt:
        logger.info("Execution interrupted by user")
        exit_code = 130

    except Exception as e:
        logger.error(f"Script execution failed: {e}", exc_info=True)
        exit_code = 1

    finally:
        # 8. Cleanup using the same event loop
        logger.debug("Cleaning up MCP connections...")
        try:
            # Run cleanup, suppressing BaseExceptionGroup from async generator cleanup
            # which can occur when contexts are entered/exited in different event loop tasks
            loop.run_until_complete(manager.cleanup())
            logger.info("Cleanup complete")
        except BaseException as e:
            # Suppress BaseExceptionGroup from async generators (harmless in cleanup)
            if type(e).__name__ == "BaseExceptionGroup":
                logger.debug("Suppressed BaseExceptionGroup during cleanup")
            else:
                logger.error(f"Cleanup failed: {e}", exc_info=True)
                if exit_code == 0:
                    exit_code = 1
        finally:
            # Close the event loop
            loop.close()

        sys.exit(exit_code)


if __name__ == "__main__":
    main()
