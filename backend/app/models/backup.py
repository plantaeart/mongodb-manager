"""Pydantic models for backups"""

from pydantic import BaseModel, Field
from datetime import datetime


class BackupCreate(BaseModel):
    """Create backup request"""
    connection_name: str = Field(..., min_length=1)


class BackupResponse(BaseModel):
    """Backup metadata response"""
    name: str
    connection: str
    created_at: datetime
    size_mb: float | None = None
    path: str


class RestoreRequest(BaseModel):
    """Restore from backup request"""
    connection_name: str = Field(..., min_length=1)
    backup_name: str = Field(..., min_length=1)


class BackupListResponse(BaseModel):
    """List of backups"""
    backups: list[BackupResponse]
    total: int
