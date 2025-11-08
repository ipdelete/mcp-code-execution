from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitFetchParams(BaseModel):
    """Parameters for git_fetch"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    remote: Optional[str] = None
    """Remote name (default: origin)."""
    prune: Optional[bool] = None
    """Prune remote-tracking references that no longer exist on remote."""
    tags: Optional[bool] = None
    """Fetch all tags from the remote."""
    depth: Optional[int] = None
    """Create a shallow clone with history truncated to N commits."""

async def git_fetch(params: GitFetchParams) -> Dict[str, Any]:
    """
    Fetch updates from a remote repository. Downloads objects and refs without merging them.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_fetch", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
