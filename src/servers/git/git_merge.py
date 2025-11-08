from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitMergeParams(BaseModel):
    """Parameters for git_merge"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    branch: str
    """Branch to merge into current branch."""
    strategy: Optional[Literal["ort", "recursive", "octopus", "ours", "subtree"]] = None
    """Merge strategy to use (ort, recursive, octopus, ours, subtree)."""
    noFastForward: Optional[bool] = None
    """Prevent fast-forward merge (create merge commit)."""
    squash: Optional[bool] = None
    """Squash all commits from the branch into a single commit."""
    message: Optional[str] = None
    """Custom merge commit message."""
    abort: Optional[bool] = None
    """Abort an in-progress merge that has conflicts."""

async def git_merge(params: GitMergeParams) -> Dict[str, Any]:
    """
    Merge branches together. Integrates changes from another branch into the current branch with optional merge strategies.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_merge", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
