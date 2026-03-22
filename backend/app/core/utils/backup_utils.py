"""Backup utility helpers for MongoDB Manager"""

from pathlib import Path


def parse_backup_selector(backup_selector: str) -> tuple[str, str]:
    """Parse a composite backup selector key into (folder_path, backup_name).

    The composite key format is ``"<folder_path>|<backup_name>"``.

    Args:
        backup_selector: Composite backup selector string.

    Returns:
        Tuple of ``(folder_path, backup_name)``.

    Raises:
        ValueError: If the selector does not contain the ``|`` separator.

    Examples:
        >>> parse_backup_selector("/backups/proj_mongodb_manager|my-backup")
        ('/backups/proj_mongodb_manager', 'my-backup')
    """
    parts = backup_selector.split("|", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid backup selector format: '{backup_selector}'")
    return parts[0], parts[1]


def collect_all_backups(connections: list[dict]) -> list[dict]:
    """Collect all backups from all configured backup paths across all connections.

    Iterates every connection's ``backup_paths`` list, asks the corresponding
    ``BackupManager`` for its backups, and returns a flat list enriched with
    ``folder_path`` and ``connection_name``.

    Imported lazily to avoid circular imports with ``app.core.backup_ops``.

    Args:
        connections: List of connection dicts as returned by
            ``ConnectionManager.list_connections()``.

    Returns:
        Flat list of backup info dicts, each containing at minimum:
        - ``backup_name`` (str)
        - ``connection_name`` (str)
        - ``folder_path`` (str)
        - ``created_at`` (str)
        - ``databases`` (list)
        - ``size`` (int)
    """
    from app.core.backup_ops import BackupManager

    all_backups: list[dict] = []

    for conn in connections:
        backup_paths: list[str] = conn.get("backup_paths", [])
        for backup_path in backup_paths:
            backup_mgr = BackupManager(Path(backup_path))
            for backup in backup_mgr.list_backups():
                all_backups.append({
                    **backup,
                    "backup_name": backup.get("backup_name", backup["name"]),
                    "connection_name": backup.get("connection_name", conn["name"]),
                    "folder_path": str(backup_path),
                })

    return all_backups
