from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitStashParams(BaseModel):
    """Parameters for git_stash"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    mode: Optional[Literal["list", "push", "pop", "apply", "drop", "clear"]] = None
    """The stash operation to perform."""
    message: Optional[str] = None
    """Stash message description (for push operation)."""
    stashRef: Optional[str] = None
    """Stash reference like stash@{0} (for pop/apply/drop operations)."""
    includeUntracked: Optional[bool] = None
    """Include untracked files in the stash (for push operation)."""
    keepIndex: Optional[bool] = None
    """Don't revert staged changes (for push operation)."""

async def git_stash(params: GitStashParams) -> Dict[str, Any]:
    """
    Manage stashes: list stashes, save current changes (push), restore changes (pop/apply), or remove stashes (drop/clear).

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_stash", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
