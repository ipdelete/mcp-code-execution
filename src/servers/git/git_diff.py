from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitDiffParams(BaseModel):
    """Parameters for git_diff"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    target: Optional[str] = None
    """Target commit/branch to compare against. If not specified, shows unstaged changes in working tree."""
    source: Optional[Dict[str, Any]] = None
    """Source commit/branch to compare from. If target is specified but not source, compares target against working tree."""
    paths: Optional[List[str]] = None
    """Limit diff to specific file paths (relative to repository root)."""
    staged: Optional[bool] = None
    """Show diff of staged changes instead of unstaged."""
    includeUntracked: Optional[bool] = None
    """Include untracked files in the diff. Useful for reviewing all upcoming changes."""
    nameOnly: Optional[bool] = None
    """Show only names of changed files, not the diff content."""
    stat: Optional[bool] = None
    """Show diffstat (summary of changes) instead of full diff content."""
    contextLines: Optional[int] = None
    """Number of context lines to show around changes."""

async def git_diff(params: GitDiffParams) -> Dict[str, Any]:
    """
    View differences between commits, branches, or working tree. Shows changes in unified diff format.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_diff", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
