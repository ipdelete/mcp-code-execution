"""Tests for the MCP execution harness."""

import os
import subprocess
from pathlib import Path

import pytest


def run_harness(script_path, cwd, env):
    """Run the harness using uv run to ensure dependencies are available."""
    return subprocess.run(
        ["uv", "run", "python", "-m", "runtime.harness", str(script_path)],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


def run_harness_no_args(cwd, env):
    """Run the harness with no arguments."""
    return subprocess.run(
        ["uv", "run", "python", "-m", "runtime.harness"],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def src_path(project_root):
    """Get the src directory path."""
    return project_root / "src"


@pytest.fixture
def test_env(src_path):
    """Get environment with PYTHONPATH set to include src directory."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_path)
    return env


@pytest.fixture
def harness_path(src_path):
    """Get the path to the harness module."""
    return src_path / "runtime" / "harness.py"


@pytest.fixture
def workspace_path(project_root):
    """Get the path to the workspace directory."""
    return project_root / "workspace"


@pytest.fixture
def test_simple_script(workspace_path):
    """Get the path to the simple test script."""
    return workspace_path / "test_simple.py"


@pytest.fixture
def test_error_script(workspace_path):
    """Get the path to the error test script."""
    return workspace_path / "test_error.py"


@pytest.fixture
def mcp_config_path(project_root):
    """Get the path to the MCP config file."""
    return project_root / "mcp_config.json"


class TestHarnessExecution:
    """Test harness script execution."""

    def test_successful_execution(self, test_simple_script, mcp_config_path, test_env):
        """Test successful script execution returns exit code 0."""
        # Ensure config exists
        assert mcp_config_path.exists(), "MCP config file should exist"

        # Run harness with simple script
        result = run_harness(test_simple_script, test_simple_script.parent.parent, test_env)

        # Check exit code
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # Check stdout contains expected output
        assert "Script started" in result.stdout
        assert "Script completed successfully" in result.stdout

        # Check stderr contains expected log messages
        assert "[INFO] Script:" in result.stderr
        assert "[INFO] MCP client manager initialized" in result.stderr
        assert "[INFO] Executing script:" in result.stderr
        assert "[INFO] Script execution completed" in result.stderr
        assert "[INFO] Cleanup complete" in result.stderr

    def test_script_not_found(self, workspace_path, mcp_config_path, test_env):
        """Test script not found returns exit code 1."""
        nonexistent_script = workspace_path / "nonexistent.py"

        result = run_harness(nonexistent_script, workspace_path.parent, test_env)

        # Check exit code
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

        # Check error message
        assert "[ERROR] Script not found:" in result.stderr

    def test_script_error_handling(self, test_error_script, mcp_config_path, test_env):
        """Test script error returns exit code 1."""
        result = run_harness(test_error_script, test_error_script.parent.parent, test_env)

        # Check exit code
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

        # Check error message
        assert "[ERROR] Script execution failed: Test error" in result.stderr
        assert "Exception: Test error" in result.stderr

        # Cleanup should still happen
        assert "[INFO] Cleanup complete" in result.stderr

    def test_no_script_argument(self, workspace_path, test_env):
        """Test no script argument returns exit code 1."""
        result = run_harness_no_args(workspace_path.parent, test_env)

        # Check exit code
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

        # Check error message
        assert "[ERROR] Usage: python -m runtime.harness <script_path>" in result.stderr

    def test_directory_as_script(self, workspace_path, test_env):
        """Test passing directory instead of file returns exit code 1."""
        result = run_harness(workspace_path, workspace_path.parent, test_env)

        # Check exit code
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

        # Check error message
        assert "[ERROR] Not a file:" in result.stderr


class TestHarnessLogging:
    """Test harness logging functionality."""

    def test_logging_to_stderr(self, test_simple_script, test_env):
        """Test that logging goes to stderr, not stdout."""
        result = run_harness(test_simple_script, test_simple_script.parent.parent, test_env)

        # Stdout should only contain script output
        assert "Script started" in result.stdout
        assert "[INFO]" not in result.stdout

        # Stderr should contain log messages
        assert "[INFO] Script:" in result.stderr
        assert "[INFO] MCP client manager initialized" in result.stderr

    def test_logging_format(self, test_simple_script, test_env):
        """Test logging format is [LEVEL] message."""
        result = run_harness(test_simple_script, test_simple_script.parent.parent, test_env)

        # Check log format
        assert "[INFO]" in result.stderr
        # Error logs in error case
        # We can verify the format exists


class TestHarnessCleanup:
    """Test harness cleanup behavior."""

    def test_cleanup_on_success(self, test_simple_script, test_env):
        """Test cleanup happens on successful execution."""
        result = run_harness(test_simple_script, test_simple_script.parent.parent, test_env)

        assert result.returncode == 0
        assert "[INFO] Cleanup complete" in result.stderr

    def test_cleanup_on_error(self, test_error_script, test_env):
        """Test cleanup happens even when script raises an exception."""
        result = run_harness(test_error_script, test_error_script.parent.parent, test_env)

        assert result.returncode == 1
        # Cleanup should still happen
        assert "[INFO] Cleanup complete" in result.stderr


class TestHarnessSysPath:
    """Test sys.path management."""

    def test_sys_path_includes_src(self, workspace_path, test_env):
        """Test that src/ is added to sys.path for imports."""
        # Create a test script that tries to import from runtime
        test_import_script = workspace_path / "test_import.py"
        test_import_script.write_text(
            """# Test script to verify sys.path includes src/
try:
    from runtime.config import McpConfig
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
    raise
"""
        )

        try:
            result = run_harness(test_import_script, workspace_path.parent, test_env)

            # Should succeed
            assert result.returncode == 0
            assert "Import successful" in result.stdout
        finally:
            # Clean up test script
            if test_import_script.exists():
                test_import_script.unlink()


class TestHarnessScriptIsolation:
    """Test script execution isolation."""

    def test_script_runs_as_main(self, workspace_path, test_env):
        """Test that script is executed with __name__ == '__main__'."""
        # Create a test script that checks __name__
        test_name_script = workspace_path / "test_name.py"
        test_name_script.write_text(
            """# Test script to verify __name__ is '__main__'
if __name__ == '__main__':
    print("Running as __main__")
else:
    print(f"Running as {__name__}")
"""
        )

        try:
            result = run_harness(test_name_script, workspace_path.parent, test_env)

            assert result.returncode == 0
            assert "Running as __main__" in result.stdout
        finally:
            # Clean up test script
            if test_name_script.exists():
                test_name_script.unlink()
