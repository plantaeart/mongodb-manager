"""Backup operation form GET population helpers"""

from app.core.utils.backup_utils import collect_all_backups
from app.core.utils.uri_builder import build_mongodb_uri_masked


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size (e.g., '1.5 GB')."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def build_backup_create_connection_options(connections: list[dict]) -> list[dict]:
    """Build select options (only connections with backup paths) for backup create step 1."""
    options = []
    for conn in connections:
        backup_paths = conn.get("backup_paths", [])
        if backup_paths:
            options.append({
                "value": conn["name"],
                "label": conn["name"],
                "description": f"Backup folders: {len(backup_paths)}",
                "metadata": {"backup_paths": backup_paths},
            })
    return options


def build_backup_list_items(connections: list[dict]) -> list[dict]:
    """Build display items for the backup list, sorted newest-first."""
    raw_backups = collect_all_backups(connections)
    all_backups = []
    for backup in raw_backups:
        all_backups.append({
            "backup_name": backup["backup_name"],
            "connection_name": backup["connection_name"],
            "created_at": backup.get("created_at", ""),
            "databases": backup.get("databases", []),
            "size": _format_size(backup.get("size", 0)),
            "folder_path": backup["folder_path"],
        })
    all_backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return all_backups


def build_backup_selector_options(connections: list[dict]) -> list[dict]:
    """Build composite-key select options for backup delete/restore selectors."""
    options = []
    for backup in collect_all_backups(connections):
        backup_name = backup["backup_name"]
        created_at = backup.get("created_at", "")
        composite_key = f"{backup['folder_path']}|{backup_name}"
        options.append({
            "value": composite_key,
            "label": f"{backup_name} ({backup['connection_name']})",
            "description": f"Created: {created_at}",
            "metadata": {
                "folder_path": backup["folder_path"],
                "backup_name": backup_name,
                "connection_name": backup["connection_name"],
            },
        })
    return options


def build_restore_selector_options(connections: list[dict]) -> list[dict]:
    """Build composite-key select options with size/db metadata for restore step 1."""
    options = []
    for backup in collect_all_backups(connections):
        backup_name = backup["backup_name"]
        created_at = backup.get("created_at", "")
        size = backup.get("size", 0)
        databases = backup.get("databases", [])
        composite_key = f"{backup['folder_path']}|{backup_name}"
        size_str = _format_size(size) if size else "Unknown"
        db_count = len(databases) if isinstance(databases, list) else 0

        options.append({
            "value": composite_key,
            "label": f"{backup_name} ({backup['connection_name']}) - {size_str}",
            "description": f"Created: {created_at} | {db_count} database(s)",
            "metadata": {
                "folder_path": backup["folder_path"],
                "backup_name": backup_name,
                "connection_name": backup["connection_name"],
                "size": size,
                "databases": databases,
                "created_at": created_at,
            },
        })
    options.sort(key=lambda x: x["metadata"].get("created_at", ""), reverse=True)
    return options


def build_restore_connection_options(connections: list[dict], original_connection: str | None) -> list[dict]:
    """Build connection select options for restore step 2, original connection listed first."""
    connection_options = []
    for conn in connections:
        masked_uri = build_mongodb_uri_masked(
            host=conn.get("host", "localhost"),
            port=conn.get("port", 27017),
            username=conn.get("username"),
            database=conn.get("database"),
            auth_source=conn.get("auth_source"),
        )
        connection_options.append({
            "value": conn["name"],
            "label": f"{conn['name']} ({masked_uri})",
            "description": conn.get("description", ""),
            "metadata": {"is_original": conn["name"] == original_connection},
        })
    connection_options.sort(
        key=lambda x: (not x["metadata"]["is_original"], x["label"])
    )
    return connection_options
