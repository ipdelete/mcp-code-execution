from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitBlameParams(BaseModel):
    """Parameters for git_blame"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    file: str
    """Path to the file to blame (relative to repository root)."""
    startLine: Optional[int] = None
    """Start line number (1-indexed)."""
    endLine: Optional[int] = None
    """End line number (1-indexed)."""
    ignoreWhitespace: Optional[bool] = None
    """Ignore whitespace changes."""

async def git_blame(params: GitBlameParams) -> Dict[str, Any]:
    """
    Show line-by-line authorship information for a file, displaying who last modified each line and when.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_blame", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
