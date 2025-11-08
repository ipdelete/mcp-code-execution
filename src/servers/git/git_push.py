from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitPushParams(BaseModel):
    """Parameters for git_push"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    remote: Optional[str] = None
    """Remote name (default: origin)."""
    branch: Optional[str] = None
    """Branch name (default: current branch)."""
    force: Optional[bool] = None
    """Force push (overwrites remote history)."""
    forceWithLease: Optional[bool] = None
    """Safer force push - only succeeds if remote branch is at expected state."""
    setUpstream: Optional[bool] = None
    """Set upstream tracking relationship for the branch."""
    tags: Optional[bool] = None
    """Push all tags to the remote."""
    dryRun: Optional[bool] = None
    """Preview the operation without executing it."""
    delete: Optional[bool] = None
    """Delete the specified remote branch."""
    remoteBranch: Optional[Dict[str, Any]] = None
    """Remote branch name to push to (if different from local branch name)."""

async def git_push(params: GitPushParams) -> Dict[str, Any]:
    """
    Push changes to a remote repository. Uploads local commits to the remote branch.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_push", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
