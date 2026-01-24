"""MongoDB connection management"""

import json
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

from .utils import get_current_time


class ConnectionManager:
    """Manages MongoDB connections configuration"""
    
    def __init__(self, config_path: Path | None = None):
        if config_path is None:
            config_path = Path.home() / ".mongodb-manager" / "connections.json"
        
        self.config_path = Path(config_path)
        self._ensure_config_exists()
    
    def _ensure_config_exists(self):
        """Create config file if it doesn't exist"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.config_path.exists():
            self.config_path.write_text(json.dumps({"connections": []}, indent=2))
    
    def _load_config(self) -> dict:
        """Load connections from config file"""
        return json.loads(self.config_path.read_text())
    
    def _save_config(self, config: dict):
        """Save connections to config file"""
        self.config_path.write_text(json.dumps(config, indent=2))
    
    def add_connection(
        self, 
        name: str, 
        uri: str, 
        description: str = ""
    ) -> bool:
        """Add a new MongoDB connection
        
        Args:
            name: Unique name for the connection
            uri: MongoDB connection URI
            description: Optional description
            
        Returns:
            True if added successfully, False if name already exists
        """
        config = self._load_config()
        
        # Check if connection name already exists
        if any(conn["name"] == name for conn in config["connections"]):
            return False
        
        connection = {
            "name": name,
            "uri": uri,
            "description": description,
            "added_at": get_current_time().isoformat(),
            "backup_paths": [],
            "active_backup_path": None
        }
        
        config["connections"].append(connection)
        self._save_config(config)
        return True
    
    def remove_connection(self, name: str) -> bool:
        """Remove a connection
        
        Args:
            name: Name of the connection to remove
            
        Returns:
            True if removed, False if not found
        """
        config = self._load_config()
        original_count = len(config["connections"])
        
        config["connections"] = [
            conn for conn in config["connections"] 
            if conn["name"] != name
        ]
        
        if len(config["connections"]) < original_count:
            self._save_config(config)
            return True
        return False
    
    def list_connections(self) -> list[dict]:
        """List all configured connections
        
        Returns:
            List of connection dictionaries
        """
        config = self._load_config()
        return config["connections"]
    
    def get_connection(self, name: str) -> dict | None:
        """Get a specific connection by name
        
        Args:
            name: Name of the connection
            
        Returns:
            Connection dict if found, None otherwise
        """
        config = self._load_config()
        
        for conn in config["connections"]:
            if conn["name"] == name:
                return conn
        return None
    
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
        
        try:
            client = MongoClient(conn["uri"], serverSelectionTimeoutMS=5000)
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
        config = self._load_config()
        
        for conn in config["connections"]:
            if conn["name"] == connection_name:
                # Initialize backup_paths if not present
                if "backup_paths" not in conn:
                    conn["backup_paths"] = []
                
                # Check if path already exists
                if path in conn["backup_paths"]:
                    return False
                
                conn["backup_paths"].append(path)
                self._save_config(config)
                return True
        
        return False
    
    def remove_backup_path(self, connection_name: str, path: str) -> bool:
        """Remove a backup path from a connection
        
        Args:
            connection_name: Name of the connection
            path: Backup folder path to remove
            
        Returns:
            True if removed successfully, False if connection or path not found
        """
        config = self._load_config()
        
        for conn in config["connections"]:
            if conn["name"] == connection_name:
                if "backup_paths" not in conn:
                    return False
                
                if path not in conn["backup_paths"]:
                    return False
                
                conn["backup_paths"].remove(path)
                
                # If this was the active path, clear it
                if conn.get("active_backup_path") == path:
                    conn["active_backup_path"] = None
                
                self._save_config(config)
                return True
        
        return False
    
    def set_active_backup_path(self, connection_name: str, path: str) -> bool:
        """Set the active backup path for a connection
        
        Args:
            connection_name: Name of the connection
            path: Backup folder path to set as active
            
        Returns:
            True if set successfully, False if connection not found or path not in backup_paths
        """
        config = self._load_config()
        
        for conn in config["connections"]:
            if conn["name"] == connection_name:
                # Initialize fields if not present
                if "backup_paths" not in conn:
                    conn["backup_paths"] = []
                
                # Verify path is in backup_paths
                if path not in conn["backup_paths"]:
                    return False
                
                conn["active_backup_path"] = path
                self._save_config(config)
                return True
        
        return False
    
    def get_backup_paths(self, connection_name: str) -> list[str]:
        """Get all backup paths for a connection
        
        Args:
            connection_name: Name of the connection
            
        Returns:
            List of backup folder paths
        """
        conn = self.get_connection(connection_name)
        if not conn:
            return []
        
        return conn.get("backup_paths", [])
    
    def get_active_backup_path(self, connection_name: str) -> str | None:
        """Get the active backup path for a connection
        
        Args:
            connection_name: Name of the connection
            
        Returns:
            Active backup path or None if not set
        """
        conn = self.get_connection(connection_name)
        if not conn:
            return None
        
        return conn.get("active_backup_path")
    
    def update_backup_path(self, connection_name: str, old_path: str, new_path: str) -> bool:
        """Update a backup path in a connection
        
        Args:
            connection_name: Name of the connection
            old_path: Existing backup folder path
            new_path: New backup folder path
            
        Returns:
            True if updated successfully, False if connection or old_path not found
        """
        config = self._load_config()
        
        for conn in config["connections"]:
            if conn["name"] == connection_name:
                if "backup_paths" not in conn:
                    return False
                
                if old_path not in conn["backup_paths"]:
                    return False
                
                # Check if new_path already exists
                if new_path in conn["backup_paths"]:
                    return False
                
                # Replace old path with new path
                idx = conn["backup_paths"].index(old_path)
                conn["backup_paths"][idx] = new_path
                
                # Update active path if it was the old path
                if conn.get("active_backup_path") == old_path:
                    conn["active_backup_path"] = new_path
                
                self._save_config(config)
                return True
        
        return False
