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


async def async_main() -> NoReturn:
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


def main() -> NoReturn:
    """Synchronous entry point that runs the async main function."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
