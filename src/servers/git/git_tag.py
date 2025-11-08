from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitTagParams(BaseModel):
    """Parameters for git_tag"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    mode: Optional[Literal["list", "create", "delete"]] = None
    """The tag operation to perform."""
    tagName: Optional[str] = None
    """Tag name for create/delete operations."""
    commit: Optional[str] = None
    """Commit to tag (default: HEAD for create operation)."""
    message: Optional[str] = None
    """Tag message (creates annotated tag)."""
    annotated: Optional[bool] = None
    """Create annotated tag with message."""
    force: Optional[bool] = None
    """Force tag creation/deletion (overwrite existing)."""

async def git_tag(params: GitTagParams) -> Dict[str, Any]:
    """
    Manage tags: list all tags, create a new tag, or delete a tag. Tags are used to mark specific points in history (releases, milestones).

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_tag", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
