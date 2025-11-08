from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitInitParams(BaseModel):
    """Parameters for git_init"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    initialBranch: Optional[str] = None
    """Name of the initial branch (default: main)."""
    bare: Optional[bool] = None
    """Create a bare repository (no working directory)."""

async def git_init(params: GitInitParams) -> Dict[str, Any]:
    """
    Initialize a new Git repository at the specified path. Creates a .git directory and sets up the initial branch.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_init", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
