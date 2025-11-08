from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitCloneParams(BaseModel):
    """Parameters for git_clone"""
    url: str
    """Remote repository URL to clone from."""
    localPath: str
    """Local path where the repository should be cloned."""
    branch: Optional[str] = None
    """Specific branch to clone (defaults to remote HEAD)."""
    depth: Optional[int] = None
    """Create a shallow clone with history truncated to N commits."""
    bare: Optional[bool] = None
    """Create a bare repository (no working directory)."""
    mirror: Optional[bool] = None
    """Create a mirror clone (implies bare)."""

async def git_clone(params: GitCloneParams) -> Dict[str, Any]:
    """
    Clone a repository from a remote URL to a local path. Supports HTTP/HTTPS and SSH URLs, with optional shallow cloning.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_clone", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
