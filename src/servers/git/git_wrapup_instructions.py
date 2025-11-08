from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from typing import Literal

class GitWrapupInstructionsParams(BaseModel):
    """Parameters for git_wrapup_instructions"""
    acknowledgement: Literal["Y", "y", "Yes", "yes"]
    """Acknowledgement to initiate the wrap-up workflow."""
    updateAgentMetaFiles: Optional[Literal["Y", "y", "Yes", "yes"]] = None
    """Include an instruction to update agent-specific meta files."""
    createTag: Optional[bool] = None
    """If true, instructs the agent to create a Git tag after committing all changes. Only set to true if given permission to do so."""

async def git_wrapup_instructions(params: GitWrapupInstructionsParams) -> Dict[str, Any]:
    """
    Provides the user's desired Git wrap-up workflow and instructions. Returns custom workflow steps (if configured) or default best practices for reviewing, documenting, and committing changes. Includes current repository status to guide next actions.

    Args:
        params: Tool parameters

    Returns:
        Tool execution result
    """
    from runtime.mcp_client import call_mcp_tool
    from runtime.normalize_fields import normalize_field_names

    # Call tool
    result = await call_mcp_tool("git__git_wrapup_instructions", params.model_dump())

    # Defensive unwrapping
    unwrapped = getattr(result, "value", result)

    # Apply field normalization
    normalized = normalize_field_names(unwrapped, "git")

    return normalized
