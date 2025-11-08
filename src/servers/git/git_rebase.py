from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitRebaseParams(BaseModel):
    """Parameters for git_rebase"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    mode: Optional[Literal["start", "continue", "abort", "skip"]] = None
    """Rebase operation mode: 'start', 'continue', 'abort', or 'skip'."""
    upstream: Optional[str] = None
    """Upstream branch to rebase onto (required for start mode)."""
    branch: Optional[Dict[str, Any]] = None
    """Branch to rebase (default: current branch)."""
    interactive: Optional[bool] = None
    """Interactive rebase (not supported in all providers)."""
    onto: Optional[Dict[str, Any]] = None
    """Rebase onto different commit than upstream."""
    preserve: Optional[bool] = None
    """Preserve merge commits during rebase."""

async def git_rebase(params: GitRebaseParams) -> Dict[str, Any]:
    """
    Rebase commits onto another branch. Reapplies commits on top of another base tip for a cleaner history.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_rebase", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
