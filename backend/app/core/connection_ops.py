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
            "added_at": get_current_time().isoformat()
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
