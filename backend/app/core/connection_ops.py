"""MongoDB connection management"""

from typing import Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

from app.repositories.connection_repository import ConnectionRepository, get_connection_repository


class ConnectionManager:
    """Manages MongoDB connections configuration
    
    This class now uses MongoDB storage via ConnectionRepository instead of JSON files.
    """
    
    def __init__(self, repository: Optional[ConnectionRepository] = None):
        """Initialize connection manager
        
        Args:
            repository: ConnectionRepository instance (defaults to global instance)
        """
        self.repository = repository or get_connection_repository()
    
    def add_connection(
        self, 
        name: str,
        host: str,
        port: int = 27017,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        auth_source: str = "admin",
        description: str = ""
    ) -> bool:
        """Add a new MongoDB connection
        
        Args:
            name: Unique name for the connection
            host: MongoDB server hostname or IP
            port: MongoDB server port (default: 27017)
            username: Username for authentication
            password: Password for authentication
            database: Default database
            auth_source: Authentication database (default: "admin")
            description: Optional description
            
        Returns:
            True if added successfully, False if name already exists
        """
        return self.repository.add_connection(
            name=name,
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            auth_source=auth_source,
            description=description
        )
    
    def remove_connection(self, name: str) -> bool:
        """Remove a connection
        
        Args:
            name: Name of the connection to remove
            
        Returns:
            True if removed, False if not found
        """
        return self.repository.remove_connection(name)
    
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
        """Update an existing MongoDB connection
        
        Args:
            name: Current name of the connection
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
        return self.repository.update_connection(
            name=name,
            new_name=new_name,
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            auth_source=auth_source,
            description=description
        )
    
    def list_connections(self) -> list[dict]:
        """List all configured connections
        
        Returns:
            List of connection dictionaries
        """
        return self.repository.list_connections()
    
    def get_connection(self, name: str) -> dict | None:
        """Get a specific connection by name
        
        Args:
            name: Name of the connection
            
        Returns:
            Connection dict if found, None otherwise
        """
        return self.repository.get_connection(name)
    
    def test_connection(self, name: str) -> tuple[bool, str]:
        """Test if a connection works
        
        Args:
            name: Name of the connection to test
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        conn = self.get_connection(name)
        if not conn:
            return False, f"Connection '{name}' not found"
        
        # Build URI from connection components
        uri = self.repository.build_uri_from_connection(conn)
        
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            # Test connection
            client.admin.command('ping')
            
            # Get server info
            server_info = client.server_info()
            version = server_info.get("version", "unknown")
            
            client.close()
            return True, f"Connected successfully (MongoDB {version})"
        
        except ConnectionFailure:
            return False, "Connection failed - cannot reach MongoDB server"
        except OperationFailure as e:
            return False, f"Authentication failed: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def test_all_connections(self) -> list[dict]:
        """Test all connections
        
        Returns:
            List of test results with name, success, and message
        """
        results = []
        for conn in self.list_connections():
            success, message = self.test_connection(conn["name"])
            results.append({
                "name": conn["name"],
                "success": success,
                "message": message
            })
        return results
    
    def add_backup_path(self, connection_name: str, path: str) -> bool:
        """Add a backup path to a connection
        
        Args:
            connection_name: Name of the connection
            path: Backup folder path to add
            
        Returns:
            True if added successfully, False if connection not found or path already exists
        """
        return self.repository.add_backup_path(connection_name, path)
    
    def remove_backup_path(self, connection_name: str, path: str) -> bool:
        """Remove a backup path from a connection
        
        Args:
            connection_name: Name of the connection
            path: Backup folder path to remove
            
        Returns:
            True if removed successfully, False if connection or path not found
        """
        return self.repository.remove_backup_path(connection_name, path)
    
    def update_backup_path(
        self, 
        connection_name: str, 
        old_path: str, 
        new_path: str
    ) -> bool:
        """Update a backup path
        
        Args:
            connection_name: Name of the connection
            old_path: Current backup folder path
            new_path: New backup folder path
            
        Returns:
            True if updated successfully, False if connection or old_path not found
        """
        return self.repository.update_backup_path(connection_name, old_path, new_path)
