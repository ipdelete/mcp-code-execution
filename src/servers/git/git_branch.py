from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitBranchParams(BaseModel):
    """Parameters for git_branch"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    operation: Optional[Literal["list", "create", "delete", "rename", "show-current"]] = None
    """The branch operation to perform."""
    name: Optional[str] = None
    """Branch name for create/delete/rename operations."""
    newName: Optional[Dict[str, Any]] = None
    """New branch name for rename operation."""
    startPoint: Optional[str] = None
    """Starting point (commit/branch) for new branch creation."""
    force: Optional[bool] = None
    """Force the operation, bypassing safety checks."""
    all: Optional[bool] = None
    """For list operation: show both local and remote branches."""
    remote: Optional[bool] = None
    """For list operation: show only remote branches."""
    merged: Optional[Dict[str, Any]] = None
    """For list operation: show only branches merged into HEAD (true) or specified commit (string)."""
    noMerged: Optional[Dict[str, Any]] = None
    """For list operation: show only branches not merged into HEAD (true) or specified commit (string)."""

async def git_branch(params: GitBranchParams) -> Dict[str, Any]:
    """
    Manage branches: list all branches, show current branch, create a new branch, delete a branch, or rename a branch.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_branch", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
