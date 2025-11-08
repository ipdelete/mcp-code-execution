from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitStatusParams(BaseModel):
    """Parameters for git_status"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    includeUntracked: Optional[bool] = None
    """Include untracked files in the output."""

async def git_status(params: GitStatusParams) -> Dict[str, Any]:
    """
    Show the working tree status including staged, unstaged, and untracked files.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_status", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
