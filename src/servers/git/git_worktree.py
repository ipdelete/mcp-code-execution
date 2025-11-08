from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitWorktreeParams(BaseModel):
    """Parameters for git_worktree"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    mode: Optional[Literal["list", "add", "remove", "move", "prune"]] = None
    """The worktree operation to perform."""
    worktreePath: Optional[str] = None
    """Path for the new worktree (for add/move operations)."""
    branch: Optional[str] = None
    """Branch to checkout in the new worktree (for add operation)."""
    commitish: Optional[str] = None
    """Commit/branch to base the worktree on (for add operation)."""
    force: Optional[bool] = None
    """Force operation (for remove operation with uncommitted changes)."""
    newPath: Optional[str] = None
    """New path for the worktree (for move operation)."""
    detach: Optional[bool] = None
    """Create worktree with detached HEAD (for add operation)."""
    verbose: Optional[bool] = None
    """Provide detailed output for worktree operations."""
    dryRun: Optional[bool] = None
    """Preview the operation without executing it (for prune operation)."""

async def git_worktree(params: GitWorktreeParams) -> Dict[str, Any]:
    """
    Manage multiple working trees: list worktrees, add new worktrees for parallel work, remove worktrees, or move worktrees to new locations.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_worktree", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
