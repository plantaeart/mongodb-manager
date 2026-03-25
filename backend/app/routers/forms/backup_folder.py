"""Backup folder form GET population helpers"""

from app.core.utils.uri_builder import build_mongodb_uri_masked


def build_backup_folder_connection_options(connections: list[dict]) -> list[dict]:
    """Build select options (connections with masked URI) for backup folder add step 2."""
    options = []
    for conn in connections:
        masked_uri = build_mongodb_uri_masked(
            host=conn.get("host", "localhost"),
            port=conn.get("port", 27017),
            username=conn.get("username"),
            database=conn.get("database"),
            auth_source=conn.get("auth_source"),
        )
        options.append({
            "value": conn["name"],
            "label": conn["name"],
            "description": masked_uri,
            "metadata": {
                "user_description": conn.get("description", ""),
            },
        })
    return options


def build_backup_folder_delete_options(connections: list[dict]) -> list[dict]:
    """Build select options (only connections that have backup folders) for delete step 1."""
    options = []
    for conn in connections:
        backup_paths = conn.get("backup_paths", [])
        if backup_paths:
            options.append({
                "value": conn["name"],
                "label": conn["name"],
                "description": f"{len(backup_paths)} backup folder(s)",
                "metadata": {
                    "backup_paths": backup_paths,
                    "description": conn.get("description", ""),
                },
            })
    return options


def build_backup_folder_list_items(connections: list[dict]) -> list[dict]:
    """Build list items for the folder list display (only connections with backup paths)."""
    items = []
    for conn in connections:
        backup_paths = conn.get("backup_paths", [])
        if backup_paths:
            items.append({
                "connection_name": conn["name"],
                "description": conn.get("description", ""),
                "backup_paths": backup_paths,
            })
    return items
