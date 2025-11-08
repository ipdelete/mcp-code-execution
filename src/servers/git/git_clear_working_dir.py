from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitClearWorkingDirParams(BaseModel):
    """Parameters for git_clear_working_dir"""
    confirm: Literal["Y", "y", "Yes", "yes"]
    """Explicit confirmation required to clear working directory. Accepted values: 'Y', 'y', 'Yes', or 'yes'."""

async def git_clear_working_dir(params: GitClearWorkingDirParams) -> Dict[str, Any]:
    """
    Clear the session working directory setting. This resets the context without restarting the server. Subsequent git operations will require an explicit path parameter unless git_set_working_dir is called again.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_clear_working_dir", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
