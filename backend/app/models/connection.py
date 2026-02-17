"""MongoDB Connection Model"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ConnectionDocument(BaseModel):
    """MongoDB document model for connection storage
    
    This model represents how connections are stored in the manager database.
    """
    name: str = Field(..., description="Unique connection name")
    uri: str = Field(..., description="MongoDB connection URI")
    description: str = Field(default="", description="Connection description")
    added_at: datetime = Field(default_factory=datetime.utcnow, description="When connection was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When connection was last updated")
    backup_paths: list[str] = Field(default_factory=list, description="List of backup folder paths")
    active_backup_path: Optional[str] = Field(default=None, description="Currently active backup path")
    created_by: str = Field(default="admin", description="User who created this connection")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "production-db",
                "uri": "mongodb://localhost:27017",
                "description": "Production database",
                "added_at": "2024-01-20T10:00:00",
                "updated_at": "2024-01-20T10:00:00",
                "backup_paths": ["/backups/prod"],
                "active_backup_path": "/backups/prod",
                "created_by": "admin"
            }
        }


class ConnectionCreate(BaseModel):
    """Model for creating a new connection"""
    name: str
    uri: str
    description: str = ""


class ConnectionUpdate(BaseModel):
    """Model for updating an existing connection"""
    new_name: Optional[str] = None
    uri: Optional[str] = None
    description: Optional[str] = None
