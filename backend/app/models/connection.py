"""MongoDB Connection Model"""

from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field


class ConnectionDocument(BaseModel):
    """MongoDB document model for connection storage
    
    This model represents how connections are stored in the manager database.
    Connections are stored as separate components (host, port, username, etc.)
    and URIs are built dynamically when needed.
    """
    name: str = Field(..., description="Unique connection name")
    host: str = Field(..., description="MongoDB server hostname or IP")
    port: int = Field(default=27017, description="MongoDB server port")
    username: str | None = Field(default=None, description="Username for authentication")
    password: str | None = Field(default=None, description="Password for authentication")
    database: str | None = Field(default=None, description="Default database")
    auth_source: str = Field(default="admin", description="Authentication database")
    description: str = Field(default="", description="Connection description")
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When connection was created")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When connection was last updated")
    backup_paths: list[str] = Field(default_factory=list, description="List of backup folder paths")
    created_by: str = Field(default="admin", description="User who created this connection")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "production-db",
                "host": "localhost",
                "port": 27017,
                "username": "admin",
                "password": "secret123",
                "database": None,
                "auth_source": "admin",
                "description": "Production database",
                "added_at": "2024-01-20T10:00:00",
                "updated_at": "2024-01-20T10:00:00",
                "backup_paths": ["/backups/prod"],
                "created_by": "admin"
            }
        }
    )


class ConnectionCreate(BaseModel):
    """Model for creating a new connection"""
    name: str
    host: str
    port: int = 27017
    username: str | None = None
    password: str | None = None
    database: str | None = None
    auth_source: str = "admin"
    description: str = ""


class ConnectionUpdate(BaseModel):
    """Model for updating an existing connection"""
    new_name: str | None = None
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    database: str | None = None
    auth_source: str | None = None
    description: str | None = None
