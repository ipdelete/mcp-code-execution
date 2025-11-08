from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitPullParams(BaseModel):
    """Parameters for git_pull"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    remote: Optional[str] = None
    """Remote name (default: origin)."""
    branch: Optional[str] = None
    """Branch name (default: current branch)."""
    rebase: Optional[bool] = None
    """Use rebase instead of merge when integrating changes."""
    fastForwardOnly: Optional[bool] = None
    """Fail if can't fast-forward (no merge commit)."""

async def git_pull(params: GitPullParams) -> Dict[str, Any]:
    """
    Pull changes from a remote repository. Fetches and integrates changes into the current branch.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_pull", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
