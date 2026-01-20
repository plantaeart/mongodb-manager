"""Pydantic models for terminal"""

from pydantic import BaseModel


class CommandExecuteRequest(BaseModel):
    """Execute command request"""
    command: str


class CommandOutputLine(BaseModel):
    """Single line of command output"""
    line: str
    timestamp: str


class CommandResult(BaseModel):
    """Command execution result"""
    success: bool
    output: list[str]
    exit_code: int
    error: str | None = None
