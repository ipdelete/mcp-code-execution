from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitCheckoutParams(BaseModel):
    """Parameters for git_checkout"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    target: Dict[str, Any]
    """Branch name, commit hash, or tag to checkout."""
    createBranch: Optional[bool] = None
    """Create a new branch with the specified name."""
    force: Optional[bool] = None
    """Force the operation, bypassing safety checks."""
    paths: Optional[List[str]] = None
    """Specific file paths to checkout/restore (relative to repository root)."""
    track: Optional[bool] = None
    """Set up tracking relationship with remote branch when creating new branch."""

async def git_checkout(params: GitCheckoutParams) -> Dict[str, Any]:
    """
    Switch branches or restore working tree files. Can checkout an existing branch, create a new branch, or restore specific files.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_checkout", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
