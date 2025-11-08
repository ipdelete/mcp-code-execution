from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitLogParams(BaseModel):
    """Parameters for git_log"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    maxCount: Optional[int] = None
    """Maximum number of items to return (1-1000)."""
    skip: Optional[int] = None
    """Number of items to skip for pagination."""
    since: Optional[str] = None
    """Show commits more recent than a specific date (ISO 8601 format)."""
    until: Optional[str] = None
    """Show commits older than a specific date (ISO 8601 format)."""
    author: Optional[str] = None
    """Filter commits by author name or email pattern."""
    grep: Optional[str] = None
    """Filter commits by message pattern (regex supported)."""
    branch: Optional[str] = None
    """Show commits from a specific branch or ref (defaults to current branch)."""
    filePath: Optional[str] = None
    """Show commits that affected a specific file path."""
    oneline: Optional[bool] = None
    """Show each commit on a single line (abbreviated output)."""
    stat: Optional[bool] = None
    """Include file change statistics for each commit."""
    patch: Optional[bool] = None
    """Include the full diff patch for each commit."""
    showSignature: Optional[bool] = None
    """Show GPG signature verification information for each commit."""

async def git_log(params: GitLogParams) -> Dict[str, Any]:
    """
    View commit history with optional filtering by author, date range, file path, or commit message pattern.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_log", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
