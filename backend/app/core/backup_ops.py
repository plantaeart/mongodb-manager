"""MongoDB backup and restore operations"""

import subprocess
import json
import shutil
from pathlib import Path

from .utils import get_current_time, get_backup_timestamp


class BackupManager:
    """Manages MongoDB backups using mongodump/mongorestore"""
    
    def __init__(self, backup_root: Path):
        """Initialize backup manager
        
        Args:
            backup_root: Root backup directory
        """
        self.backup_root = Path(backup_root)
    
    def init_backup_folder(self) -> Path:
        """Create root backup folder
        
        Returns:
            Path to created backup folder
        """
        self.backup_root.mkdir(parents=True, exist_ok=True)
        return self.backup_root
    
    def create_backup(self, connection_uri: str, connection_name: str, backup_name: str) -> Path:
        """Backup MongoDB using mongodump
        
        Args:
            connection_uri: MongoDB connection URI
            connection_name: Name of the connection being backed up
            backup_name: Custom name for the backup (required, must be unique)
            
        Returns:
            Path to created backup folder
            
        Raises:
            ValueError: If backup_name already exists or is invalid
            Exception: If mongodump fails
        """
        # Validate backup name doesn't exist
        backup_path = self.backup_root / backup_name
        if backup_path.exists():
            raise ValueError(f"Backup '{backup_name}' already exists in {self.backup_root}")
        
        # Create backup folder
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Run mongodump
        cmd = [
            "mongodump",
            f"--uri={connection_uri}",
            f"--out={backup_path}",
            "--oplog",
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Cleanup failed backup
            shutil.rmtree(backup_path, ignore_errors=True)
            raise Exception(f"mongodump failed: {result.stderr}")
        
        # Get list of databases backed up
        databases = [d.name for d in backup_path.iterdir() if d.is_dir()]
        
        # Get timestamp for metadata
        timestamp = get_backup_timestamp()
        
        # Save metadata
        metadata = {
            "connection_name": connection_name,
            "backup_name": backup_name,
            "timestamp": timestamp,
            "created_at": get_current_time().isoformat(),
            "databases": databases,
        }
        
        (backup_path / "metadata.json").write_text(json.dumps(metadata, indent=2))
        
        return backup_path
    
    def list_backups(self) -> list[dict]:
        """List all backup folders
        
        Returns:
            List of backup information dictionaries
        """
        if not self.backup_root.exists():
            return []
        
        backups = []
        for backup_dir in sorted(self.backup_root.iterdir(), reverse=True):
            if not backup_dir.is_dir():
                continue
            
            metadata_file = backup_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    metadata = json.loads(metadata_file.read_text())
                except json.JSONDecodeError:
                    metadata = {
                        "connection_name": "unknown",
                        "timestamp": "",
                        "databases": []
                    }
            else:
                metadata = {
                    "connection_name": "unknown",
                    "timestamp": "",
                    "databases": []
                }
            
            backups.append({
                "name": backup_dir.name,
                "path": backup_dir,
                "connection_name": metadata.get("connection_name", "unknown"),
                "timestamp": metadata.get("timestamp", ""),
                "created_at": metadata.get("created_at", ""),
                "databases": metadata.get("databases", []),
            })
        
        return backups
    
    def restore_backup(
        self, 
        backup_path: Path, 
        connection_uri: str, 
        drop: bool = False
    ):
        """Restore MongoDB using mongorestore
        
        Args:
            backup_path: Path to backup folder
            connection_uri: MongoDB connection URI to restore to
            drop: Whether to drop existing collections before restore
            
        Raises:
            Exception: If mongorestore fails
        """
        cmd = [
            "mongorestore",
            f"--uri={connection_uri}",
            str(backup_path),
            "--oplogReplay",
        ]
        
        if drop:
            cmd.append("--drop")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"mongorestore failed: {result.stderr}")
    
    def delete_backup(self, backup_name: str):
        """Delete a backup folder
        
        Args:
            backup_name: Name of the backup folder to delete
        """
        backup_path = self.backup_root / backup_name
        if backup_path.exists() and backup_path.is_dir():
            shutil.rmtree(backup_path)
    
    def delete_all_backups(self):
        """Delete all backup folders"""
        for backup in self.list_backups():
            self.delete_backup(backup["name"])
