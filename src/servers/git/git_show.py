from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitShowParams(BaseModel):
    """Parameters for git_show"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    object: str
    """Git object to show (commit hash, branch, tag, tree, or blob)."""
    format: Optional[Literal["raw", "json"]] = None
    """Output format for the git object."""
    stat: Optional[bool] = None
    """Show diffstat instead of full diff."""
    filePath: Optional[str] = None
    """View specific file at a given commit reference. When provided, shows the file content from the specified object."""

async def git_show(params: GitShowParams) -> Dict[str, Any]:
    """
    Show details of a git object (commit, tree, blob, or tag). Displays commit information and the diff of changes introduced.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_show", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
