"""MongoDB connection management"""

from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

from app.repositories.connection_repository import ConnectionRepository, get_connection_repository, _UNSET
from app.enums import MongoDefault, MongoTool


class ConnectionManager:
    """Manages MongoDB connections configuration
    
    This class now uses MongoDB storage via ConnectionRepository instead of JSON files.
    """
    
    def __init__(self, repository: ConnectionRepository | None = None):
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
        username: str | None = None,
        password: str | None = None,
        database: str | None = None,
        auth_source: str | None = None,
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
            auth_source: Authentication database (None = no authSource in URI)
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
        new_name: str | None = None,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        database: str | None = None,
        auth_source: str | None = _UNSET,  # type: ignore[assignment]
        description: str | None = None
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
            auth_source: New auth_source; None clears it; omit to keep current
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
            client = MongoClient(uri, serverSelectionTimeoutMS=MongoDefault.SERVER_TIMEOUT_MS)
            # Test connection
            client.admin.command(MongoTool.PING)
            
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

    # -------------------------------------------------------------------------
    # Export / Import
    # -------------------------------------------------------------------------

    def export_connections(self) -> list[dict]:
        """Return all connections as a list of dicts, with passwords stripped.

        The exported data is safe to share — passwords are removed entirely.
        All other fields (including backup_paths) are preserved so the export
        can be used for a full round-trip import on another instance.

        Returns:
            List of connection dicts without the 'password' field
        """
        connections = self.list_connections()
        sanitized: list[dict] = []
        for conn in connections:
            c = dict(conn)
            c.pop("password", None)
            # Remove MongoDB internal _id if present
            c.pop("_id", None)
            sanitized.append(c)
        return sanitized

    @staticmethod
    def _ensure_backup_paths(backup_paths: list[str]) -> list[str]:
        """Ensure each backup folder path exists, creating it if necessary.

        Args:
            backup_paths: List of folder path strings from import data.

        Returns:
            The same list (paths that could not be created are skipped silently).
        """
        valid: list[str] = []
        for raw_path in backup_paths:
            if not raw_path or not raw_path.strip():
                continue
            try:
                p = Path(raw_path)
                p.mkdir(parents=True, exist_ok=True)
                valid.append(raw_path)
            except Exception:
                # Path is invalid or not writable — skip it
                pass
        return valid

    def import_connections(
        self,
        connections: list[dict],
        overwrite: bool = False,
        import_backup_paths: bool = False,
    ) -> dict:
        """Import a list of connection dicts.

        Args:
            connections: List of connection dicts (as produced by export_connections)
            overwrite: When True, existing connections with the same name are updated.
                       When False, duplicates are silently skipped.
            import_backup_paths: When True, preserve backup_paths from the import data.
                                 Each path is created on disk if it does not already exist.
                                 When False, backup_paths are stripped (default safe behaviour).

        Returns:
            Summary dict::

                {
                    "imported": <int>,   # newly added
                    "overwritten": <int>,# updated (only when overwrite=True)
                    "skipped": <int>,    # duplicates ignored
                    "errors": [<str>]    # per-connection error messages
                }
        """
        imported = 0
        overwritten = 0
        skipped = 0
        errors: list[str] = []

        for conn in connections:
            name = conn.get("name", "").strip()
            if not name:
                errors.append("Skipped entry with missing or empty 'name' field")
                skipped += 1
                continue

            host = conn.get("host", "localhost")
            port = conn.get("port", 27017)

            # Strip backup_paths unless requested; auto-create folders when kept
            raw_paths: list[str] = conn.get("backup_paths", []) if import_backup_paths else []
            backup_paths: list[str] = self._ensure_backup_paths(raw_paths) if raw_paths else []

            existing = self.get_connection(name)

            if existing:
                if not overwrite:
                    skipped += 1
                    continue

                # Overwrite: update all updatable fields
                try:
                    success = self.repository.update_connection(
                        name=name,
                        host=host,
                        port=int(port),
                        username=conn.get("username"),
                        password=conn.get("password"),  # may be None / absent
                        database=conn.get("database"),
                        auth_source=conn.get("auth_source"),
                        description=conn.get("description", ""),
                    )
                    if success:
                        # Sync backup_paths: replace entirely
                        # First clear existing paths, then add new ones
                        for bp in existing.get("backup_paths", []):
                            self.repository.remove_backup_path(name, bp)
                        for bp in backup_paths:
                            self.repository.add_backup_path(name, bp)
                        overwritten += 1
                    else:
                        errors.append(f"Failed to overwrite connection '{name}'")
                except Exception as exc:
                    errors.append(f"Error overwriting '{name}': {exc}")
                continue

            # New connection
            try:
                added = self.repository.add_connection(
                    name=name,
                    host=host,
                    port=int(port),
                    username=conn.get("username"),
                    password=conn.get("password"),
                    database=conn.get("database"),
                    auth_source=conn.get("auth_source"),
                    description=conn.get("description", ""),
                )
                if added:
                    for bp in backup_paths:
                        self.repository.add_backup_path(name, bp)
                    imported += 1
                else:
                    # Race condition: name appeared between get and add
                    skipped += 1
            except Exception as exc:
                errors.append(f"Error importing '{name}': {exc}")

        return {
            "imported": imported,
            "overwritten": overwritten,
            "skipped": skipped,
            "errors": errors,
        }
