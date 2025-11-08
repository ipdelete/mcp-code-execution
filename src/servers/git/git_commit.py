from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitCommitParams(BaseModel):
    """Parameters for git_commit"""
    path: Optional[str] = None
    """Path to the Git repository. Defaults to session working directory set via git_set_working_dir."""
    message: str
    """Commit message."""
    author: Optional[Dict[str, Any]] = None
    """Override commit author (defaults to git config)."""
    amend: Optional[bool] = None
    """Amend the previous commit instead of creating a new one. Use with caution."""
    allowEmpty: Optional[bool] = None
    """Allow creating a commit with no changes."""
    sign: Optional[bool] = None
    """Sign the commit/tag with GPG."""
    noVerify: Optional[bool] = None
    """Bypass pre-commit and commit-msg hooks."""
    filesToStage: Optional[List[str]] = None
    """File paths to stage before committing (atomic stage+commit operation)."""
    forceUnsignedOnFailure: Optional[bool] = None
    """If GPG/SSH signing fails, retry the commit without signing instead of failing."""

async def git_commit(params: GitCommitParams) -> Dict[str, Any]:
    """
    Create a new commit with staged changes in the repository. Records a snapshot of the staging area with a commit message.

**Commit Message Format:**
Pass commit messages as JSON string parameters. Multi-line messages are supported using standard JSON string escaping.

**Examples:**
- Single line: { "message": "feat: add user authentication" }
- Multi-line: { "message": "feat: add user authentication\n\nImplemented OAuth2 flow with JWT tokens.\nAdded tests for login and logout." }

Note: Do not use bash heredoc syntax.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_commit", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
