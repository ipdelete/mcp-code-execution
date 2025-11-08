"""Pytest configuration for integration tests."""

import pytest

from runtime.mcp_client import get_mcp_client_manager


@pytest.fixture(autouse=True)
async def cleanup_mcp_manager():
    """Cleanup MCP client manager after each test.

    This fixture ensures that:
    1. Each test gets a fresh manager instance
    2. The singleton cache is cleared between tests
    3. All connections are properly closed

    This is critical because get_mcp_client_manager() uses @lru_cache
    which would otherwise share state across all tests.
    """
    # Yield to run the test
    yield

    # Cleanup after test
    try:
        manager = get_mcp_client_manager()
        # Only cleanup if manager was initialized
        if manager._state.value != "uninitialized":
            await manager.cleanup()
    except Exception as e:
        # Log but don't fail if cleanup has issues
        print(f"Warning: Manager cleanup failed: {e}")
    finally:
        # Clear the lru_cache to ensure next test gets fresh instance
        get_mcp_client_manager.cache_clear()
