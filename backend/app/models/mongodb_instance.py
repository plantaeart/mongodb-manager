"""
MongoDB Instance Model

Represents a discovered MongoDB instance with connection details
and utility methods for connection management.
"""

from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError


class MongoDBInstance(BaseModel):
    """Represents a discovered MongoDB instance"""
    
    host: str = Field(..., description="IP address or hostname")
    port: int = Field(..., description="Port number")
    version: str | None = Field(None, description="MongoDB version")
    detected: bool = Field(False, description="Successfully detected as MongoDB")
    requires_auth: bool = Field(True, description="Authentication required")
    connection_uri: str = Field("", description="Generated connection URI")
    server_info: dict = Field(default_factory=dict, description="Server metadata")
    container_name: str | None = Field(None, description="Docker container name if available")
    
    def get_display_name(self) -> str:
        """
        Generate display name for selection menus
        
        Returns:
            Formatted string with container name or host:port
        """
        if self.container_name:
            if self.version:
                return f"{self.container_name} ({self.host}:{self.port}) - MongoDB v{self.version}"
            else:
                return f"{self.container_name} ({self.host}:{self.port}) - MongoDB"
        elif self.version:
            return f"{self.host}:{self.port} - MongoDB v{self.version}"
        else:
            return f"{self.host}:{self.port} - MongoDB (Unknown version)"
    
    def get_short_name(self) -> str:
        """
        Get short name for table display
        
        Returns:
            Container name if available, otherwise host:port
        """
        return self.container_name or f"{self.host}:{self.port}"
    
    def get_connection_uri(
        self,
        username: str = "",
        password: str = "",
        auth_source: str = "admin",
        ssl: bool = False,
        direct_connection: bool = True
    ) -> str:
        """
        Generate MongoDB connection URI
        
        Args:
            username: MongoDB username (optional)
            password: MongoDB password (optional)
            auth_source: Authentication database (default: "admin")
            ssl: Enable SSL/TLS (default: False)
            direct_connection: Use direct connection mode (default: True)
        
        Returns:
            MongoDB connection URI string
        """
        # Build credentials part
        if username and password:
            credentials = f"{username}:{password}@"
        else:
            credentials = ""
        
        # Build options part
        options = []
        if auth_source and username:
            options.append(f"authSource={auth_source}")
        if direct_connection:
            options.append("directConnection=true")
        if ssl:
            options.append("tls=true")
        
        options_str = "?" + "&".join(options) if options else ""
        
        # Build full URI
        uri = f"mongodb://{credentials}{self.host}:{self.port}{options_str}"
        
        return uri
    
    def test_connection(
        self,
        username: str = "",
        password: str = "",
        auth_source: str = "admin",
        timeout: int = 5
    ) -> tuple[bool, str]:
        """
        Test connection with optional credentials
        
        Args:
            username: MongoDB username (optional)
            password: MongoDB password (optional)
            auth_source: Authentication database (default: "admin")
            timeout: Connection timeout in seconds (default: 5)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        uri = self.get_connection_uri(username, password, auth_source)
        
        try:
            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=timeout * 1000,
                connectTimeoutMS=timeout * 1000
            )
            
            # Try to get server info
            info = client.server_info()
            version = info.get("version", "unknown")
            
            # Try to list databases (will fail if no auth but connection works)
            try:
                client.list_database_names()
                return (True, f"Connected successfully to MongoDB v{version}")
            except OperationFailure as e:
                if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                    return (False, f"Authentication failed: {e}")
                return (False, f"Permission error: {e}")
            
        except ServerSelectionTimeoutError:
            return (False, f"Connection timeout - server not reachable at {self.host}:{self.port}")
        except ConnectionFailure as e:
            return (False, f"Connection failed: {e}")
        except Exception as e:
            return (False, f"Error: {e}")
        finally:
            try:
                client.close()
            except:
                pass
    
    def get_location_type(self) -> str:
        """
        Determine if this is a localhost or network instance
        
        Returns:
            "localhost" if host is localhost/127.0.0.1, otherwise "network"
        """
        if self.host in ["localhost", "127.0.0.1", "::1"]:
            return "localhost"
        return "network"
    
    def get_short_description(self) -> str:
        """
        Get short description for table display
        
        Returns:
            String describing the instance
        """
        location = self.get_location_type()
        version_str = f"v{self.version}" if self.version else "Unknown"
        auth_str = "Auth Required" if self.requires_auth else "No Auth"
        
        return f"{location.capitalize()} | {version_str} | {auth_str}"
    
    def to_connection_dict(self, name: str, description: str = "") -> dict:
        """
        Convert to connection dictionary for ConnectionManager
        
        Args:
            name: Connection name
            description: Connection description (optional)
        
        Returns:
            Dictionary compatible with ConnectionManager.add_connection()
        """
        return {
            "name": name,
            "uri": self.connection_uri,
            "description": description or f"Discovered MongoDB at {self.host}:{self.port}",
        }
