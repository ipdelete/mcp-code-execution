from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitAddParams(BaseModel):
    """Parameters for git_add"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    files: List[str]
    """Array of file paths to stage (relative to repository root). Use ["."] to stage all changes."""
    update: Optional[bool] = None
    """Stage only modified and deleted files (skip untracked files)."""
    all: Optional[bool] = None
    """Include all items (varies by operation)."""
    force: Optional[bool] = None
    """Allow adding otherwise ignored files."""

async def git_add(params: GitAddParams) -> Dict[str, Any]:
    """
    Stage files for commit. Add file contents to the staging area (index) to prepare for the next commit.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_add", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
