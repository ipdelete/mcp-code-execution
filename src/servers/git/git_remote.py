from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitRemoteParams(BaseModel):
    """Parameters for git_remote"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    mode: Optional[Literal["list", "add", "remove", "rename", "get-url", "set-url"]] = None
    """The remote operation to perform."""
    name: Optional[str] = None
    """Remote name for add/remove/rename/get-url/set-url operations."""
    url: Optional[str] = None
    """Remote URL for add/set-url operations."""
    newName: Optional[Dict[str, Any]] = None
    """New remote name for rename operation."""
    push: Optional[bool] = None
    """Set push URL separately (for set-url operation)."""

async def git_remote(params: GitRemoteParams) -> Dict[str, Any]:
    """
    Manage remote repositories: list remotes, add new remotes, remove remotes, rename remotes, or get/set remote URLs.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_remote", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
