from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitResetParams(BaseModel):
    """Parameters for git_reset"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    mode: Optional[Literal["soft", "mixed", "hard", "merge", "keep"]] = None
    """Reset mode: soft (keep changes staged), mixed (unstage changes), hard (discard all changes), merge (reset and merge), keep (reset but keep local changes)."""
    target: Optional[str] = None
    """Target commit to reset to (default: HEAD)."""
    paths: Optional[List[str]] = None
    """Specific file paths to reset (leaves HEAD unchanged)."""

async def git_reset(params: GitResetParams) -> Dict[str, Any]:
    """
    Reset current HEAD to specified state. Can be used to unstage files (soft), discard commits (mixed), or discard all changes (hard).

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_reset", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
