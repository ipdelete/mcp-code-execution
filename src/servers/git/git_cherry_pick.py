from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitCherryPickParams(BaseModel):
    """Parameters for git_cherry_pick"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    commits: List[str]
    """Commit hashes to cherry-pick."""
    noCommit: Optional[bool] = None
    """Don't create commit (stage changes only)."""
    continueOperation: Optional[bool] = None
    """Continue cherry-pick after resolving conflicts."""
    abort: Optional[bool] = None
    """Abort cherry-pick operation."""
    mainline: Optional[int] = None
    """For merge commits, specify which parent to follow (1 for first parent, 2 for second, etc.)."""
    strategy: Optional[Literal["ort", "recursive", "octopus", "ours", "subtree"]] = None
    """Merge strategy to use for cherry-pick."""
    signoff: Optional[bool] = None
    """Add Signed-off-by line to the commit message."""

async def git_cherry_pick(params: GitCherryPickParams) -> Dict[str, Any]:
    """
    Cherry-pick commits from other branches. Apply specific commits to the current branch without merging entire branches.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_cherry_pick", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
