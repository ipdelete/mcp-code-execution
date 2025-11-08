"""
Discovered Pydantic models for git server.

WARNING: These models are inferred from actual API responses.
They may be incomplete or incorrect. Use with caution.
All fields are Optional for defensive coding.
"""

from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class GitStatusResult(BaseModel):
    """Result from git_status tool."""
    branch: Optional[str] = None
    ahead: Optional[int] = None
    behind: Optional[int] = None
    staged: Optional[List[str]] = None
    unstaged: Optional[List[str]] = None
    untracked: Optional[List[str]] = None


class GitLogResult(BaseModel):
    """Result from git_log tool."""
    commit: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    message: Optional[str] = None
