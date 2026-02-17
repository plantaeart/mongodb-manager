"""Pydantic models for connections"""

from pydantic import BaseModel, Field
from datetime import datetime


class ConnectionCreate(BaseModel):
    """Create new connection"""
    name: str = Field(..., min_length=1)
    uri: str = Field(..., min_length=1)
    description: str | None = None
    backup_paths: list[str] = []
    active_backup_path: str | None = None


class ConnectionUpdate(BaseModel):
    """Update connection"""
    name: str | None = None  # For renaming connection
    uri: str | None = None
    description: str | None = None
    backup_paths: list[str] | None = None
    active_backup_path: str | None = None


class ConnectionResponse(BaseModel):
    """Connection response"""
    name: str
    uri: str
    description: str | None
    created_at: datetime
    last_tested: datetime | None = None
    status: str | None = None
    backup_paths: list[str] = []
    active_backup_path: str | None = None


class ConnectionTestResponse(BaseModel):
    """Connection test response"""
    success: bool
    message: str
    latency_ms: float | None = None
