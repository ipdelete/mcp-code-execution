from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitSetWorkingDirParams(BaseModel):
    """Parameters for git_set_working_dir"""
    path: str
    """Absolute path to the git repository to use as the working directory."""
    validateGitRepo: Optional[bool] = None
    """Validate that the path is a Git repository."""
    initializeIfNotPresent: Optional[bool] = None
    """If not a Git repository, initialize it with 'git init'."""
    includeMetadata: Optional[bool] = None
    """Include repository metadata (status, branches, remotes, recent commits) in the response. Set to true for immediate repository context understanding. Defaults to false to minimize response size."""

async def git_set_working_dir(params: GitSetWorkingDirParams) -> Dict[str, Any]:
    """
    Set the session working directory for all git operations. This allows subsequent git commands to omit the path parameter and use this directory as the default.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_set_working_dir", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
