"""Request/response models for command execution"""

from typing import Any
from pydantic import BaseModel


class CommandExecuteRequest(BaseModel):
    """Request model for command execution"""
    command: str  # e.g., "connect add"
    params: dict[str, Any]  # e.g., {"name": "my-db", "uri": "mongodb://..."}


class CommandExecuteResponse(BaseModel):
    """Response model for command execution"""
    success: bool
    output: str
    error: str | None = None
    exit_code: int = 0
