"""Connection Repository for MongoDB CRUD Operations

This repository provides all database operations for managing connections.
"""

from datetime import datetime, timezone
from typing import Optional
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.core.database import get_manager_db
from app.models.connection import ConnectionDocument


class ConnectionRepository:
    """Repository for connection CRUD operations"""
    
    def __init__(self, db: Optional[Database] = None):
        """Initialize repository
        
        Args:
            db: MongoDB database instance (defaults to manager db)
        """
        self.db = db or get_manager_db()
        self.collection = self.db.connections
    
    def add_connection(
        self, 
        name: str,
        host: str,
        port: int = 27017,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        auth_source: str = "admin",
        description: str = "",
        created_by: str = "admin"
    ) -> bool:
        """Add a new connection
        
        Args:
            name: Unique connection name
            host: MongoDB server hostname or IP
            port: MongoDB server port (default: 27017)
            username: Username for authentication
            password: Password for authentication
            database: Default database
            auth_source: Authentication database (default: "admin")
            description: Optional description
            created_by: User who created the connection
            
        Returns:
            True if added successfully, False if name already exists
        """
        try:
            connection = ConnectionDocument(
                name=name,
                host=host,
                port=port,
                username=username,
                password=password,
                database=database,
                auth_source=auth_source,
                description=description,
                added_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                backup_paths=[],
                active_backup_path=None,
                created_by=created_by
            )
            
            self.collection.insert_one(connection.model_dump())
            return True
            
        except DuplicateKeyError:
            # Connection name already exists
            return False
    
    def get_connection(self, name: str) -> Optional[dict]:
        """Get a connection by name
        
        Args:
            name: Connection name
            
        Returns:
            Connection dict if found, None otherwise
        """
        return self.collection.find_one({"name": name}, {"_id": 0})
    
    def list_connections(self) -> list[dict]:
        """List all connections
        
        Returns:
            List of connection dictionaries, sorted by name
        """
        return list(self.collection.find({}, {"_id": 0}).sort("name", 1))
    
    def update_connection(
        self,
        name: str,
        new_name: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        auth_source: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """Update an existing connection
        
        Args:
            name: Current connection name
            new_name: New name (if renaming), None to keep current
            host: New host, None to keep current
            port: New port, None to keep current
            username: New username, None to keep current
            password: New password, None to keep current
            database: New database, None to keep current
            auth_source: New auth_source, None to keep current
            description: New description, None to keep current
            
        Returns:
            True if updated successfully, False if not found or new_name already exists
        """
        # Check if connection exists
        if not self.get_connection(name):
            return False
        
        # If renaming, check new name doesn't exist
        if new_name and new_name != name:
            if self.get_connection(new_name):
                return False
        
        # Build update document
        update_doc = {"updated_at": datetime.now(timezone.utc)}
        
        if new_name and new_name != name:
            update_doc["name"] = new_name
        
        if host is not None:
            update_doc["host"] = host
        
        if port is not None:
            update_doc["port"] = port
        
        if username is not None:
            update_doc["username"] = username
        
        if password is not None:
            update_doc["password"] = password
        
        if database is not None:
            update_doc["database"] = database
        
        if auth_source is not None:
            update_doc["auth_source"] = auth_source
        
        if description is not None:
            update_doc["description"] = description
        
        # Perform update
        result = self.collection.update_one(
            {"name": name},
            {"$set": update_doc}
        )
        
        return result.modified_count > 0 or result.matched_count > 0
    
    def build_uri_from_connection(self, connection: dict) -> str:
        """Build MongoDB URI from connection components
        
        Args:
            connection: Connection dictionary with components
            
        Returns:
            Complete MongoDB connection URI
        """
        from app.core.utils.uri_builder import build_mongodb_uri
        
        return build_mongodb_uri(
            host=connection.get("host", "localhost"),
            port=connection.get("port", 27017),
            username=connection.get("username"),
            password=connection.get("password"),
            database=connection.get("database"),
            auth_source=connection.get("auth_source", "admin")
        )
    
    def remove_connection(self, name: str) -> bool:
        """Remove a connection
        
        Args:
            name: Connection name
            
        Returns:
            True if removed, False if not found
        """
        result = self.collection.delete_one({"name": name})
        return result.deleted_count > 0
    
    def add_backup_path(self, connection_name: str, path: str) -> bool:
        """Add a backup path to a connection
        
        Args:
            connection_name: Connection name
            path: Backup folder path
            
        Returns:
            True if added, False if connection not found or path already exists
        """
        # Check if connection exists
        connection = self.get_connection(connection_name)
        if not connection:
            return False
        
        # Check if path already exists
        if path in connection.get("backup_paths", []):
            return False
        
        # Add path
        result = self.collection.update_one(
            {"name": connection_name},
            {
                "$push": {"backup_paths": path},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        
        return result.modified_count > 0
    
    def remove_backup_path(self, connection_name: str, path: str) -> bool:
        """Remove a backup path from a connection
        
        Args:
            connection_name: Connection name
            path: Backup folder path
            
        Returns:
            True if removed, False if connection or path not found
        """
        # Check if connection exists
        connection = self.get_connection(connection_name)
        if not connection:
            return False
        
        # Check if path exists
        if path not in connection.get("backup_paths", []):
            return False
        
        # Remove path
        update_ops = {
            "$pull": {"backup_paths": path},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
        
        # If this was the active path, clear it
        if connection.get("active_backup_path") == path:
            update_ops["$set"]["active_backup_path"] = None
        
        result = self.collection.update_one(
            {"name": connection_name},
            update_ops
        )
        
        return result.modified_count > 0
    
    def set_active_backup_path(self, connection_name: str, path: str) -> bool:
        """Set the active backup path for a connection
        
        Args:
            connection_name: Connection name
            path: Backup folder path to set as active
            
        Returns:
            True if set, False if connection not found or path not in backup_paths
        """
        # Check if connection exists
        connection = self.get_connection(connection_name)
        if not connection:
            return False
        
        # Check if path is in backup_paths
        if path not in connection.get("backup_paths", []):
            return False
        
        # Set active path
        result = self.collection.update_one(
            {"name": connection_name},
            {
                "$set": {
                    "active_backup_path": path,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return result.modified_count > 0
    
    def update_backup_path(
        self, 
        connection_name: str, 
        old_path: str, 
        new_path: str
    ) -> bool:
        """Update a backup path
        
        Args:
            connection_name: Connection name
            old_path: Current backup path
            new_path: New backup path
            
        Returns:
            True if updated, False if connection or old_path not found
        """
        # Check if connection exists
        connection = self.get_connection(connection_name)
        if not connection:
            return False
        
        # Check if old path exists
        if old_path not in connection.get("backup_paths", []):
            return False
        
        # Update path in array
        update_ops = {
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
        
        # Pull old path and push new path
        self.collection.update_one(
            {"name": connection_name},
            {"$pull": {"backup_paths": old_path}}
        )
        
        result = self.collection.update_one(
            {"name": connection_name},
            {
                "$push": {"backup_paths": new_path},
                "$set": update_ops["$set"]
            }
        )
        
        # If old_path was active, update to new_path
        if connection.get("active_backup_path") == old_path:
            self.collection.update_one(
                {"name": connection_name},
                {"$set": {"active_backup_path": new_path}}
            )
        
        return result.modified_count > 0


# Global repository instance
_repository: Optional[ConnectionRepository] = None


def get_connection_repository() -> ConnectionRepository:
    """Get the global connection repository instance
    
    Returns:
        ConnectionRepository instance
    """
    global _repository
    if _repository is None:
        _repository = ConnectionRepository()
    return _repository
