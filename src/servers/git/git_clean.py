from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitCleanParams(BaseModel):
    """Parameters for git_clean"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    force: bool
    """Force the operation, bypassing safety checks."""
    dryRun: Optional[bool] = None
    """Preview the operation without executing it."""
    directories: Optional[bool] = None
    """Remove untracked directories in addition to files."""
    ignored: Optional[bool] = None
    """Remove ignored files as well."""

async def git_clean(params: GitCleanParams) -> Dict[str, Any]:
    """
    Remove untracked files from the working directory. Requires force flag for safety. Use dry-run to preview files that would be removed.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_clean", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
