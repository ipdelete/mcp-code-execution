from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitReflogParams(BaseModel):
    """Parameters for git_reflog"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    ref: Optional[str] = None
    """Show reflog for specific reference (default: HEAD)."""
    maxCount: Optional[int] = None
    """Maximum number of items to return (1-1000)."""

async def git_reflog(params: GitReflogParams) -> Dict[str, Any]:
    """
    View the reference logs (reflog) to track when branch tips and other references were updated. Useful for recovering lost commits.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_reflog", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
