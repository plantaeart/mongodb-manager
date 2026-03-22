"""Backup operation command handlers (create and restore)"""

from pathlib import Path

from app.core.connection_ops import ConnectionManager
from app.core.backup_ops import BackupManager
from app.routers.commands.models import CommandExecuteResponse
from app.core.utils.backup_utils import parse_backup_selector


def handle_backup_create(params: dict) -> CommandExecuteResponse:
    """Create a new backup for a connection"""
    connection_name = params.get("connection_name")
    backup_name = params.get("backup_name")
    backup_location = params.get("backup_location")

    if not connection_name:
        return CommandExecuteResponse(
            success=False, output="", error="Connection name is required", exit_code=1
        )
    if not backup_name:
        return CommandExecuteResponse(
            success=False, output="", error="Backup name is required", exit_code=1
        )
    if not backup_location:
        return CommandExecuteResponse(
            success=False, output="", error="Backup location is required", exit_code=1
        )

    conn_mgr = ConnectionManager()

    connection = conn_mgr.get_connection(connection_name)
    if not connection:
        return CommandExecuteResponse(
            success=False,
            output="",
            error=f"Connection '{connection_name}' not found",
            exit_code=1,
        )

    backup_paths = connection.get("backup_paths", [])
    if backup_location not in backup_paths:
        return CommandExecuteResponse(
            success=False,
            output="",
            error="Invalid backup location. Must be one of the configured backup folders.",
            exit_code=1,
        )

    connection_uri = conn_mgr.repository.build_uri_from_connection(connection)
    backup_mgr = BackupManager(Path(backup_location))

    try:
        backup_path = backup_mgr.create_backup(connection_uri, connection_name, backup_name)
        return CommandExecuteResponse(
            success=True,
            output=f"✓ Backup '{backup_name}' created successfully at {backup_path}",
            error=None,
            exit_code=0,
        )
    except ValueError as e:
        return CommandExecuteResponse(
            success=False, output="", error=str(e), exit_code=1
        )
    except Exception as e:
        return CommandExecuteResponse(
            success=False, output="", error=f"Backup failed: {str(e)}", exit_code=1
        )


def handle_backup_restore(params: dict) -> CommandExecuteResponse:
    """Restore a backup to a connection"""
    backup_selector = params.get("backup_selector")
    connection_name = params.get("connection_name")
    drop_collections = params.get("drop_collections", False)
    confirmation = params.get("confirmation", False)

    if not backup_selector:
        return CommandExecuteResponse(
            success=False, output="", error="Backup selector is required", exit_code=1
        )
    if not connection_name:
        return CommandExecuteResponse(
            success=False, output="", error="Connection name is required", exit_code=1
        )
    if not confirmation:
        return CommandExecuteResponse(
            success=False, output="", error="You must confirm the restore operation", exit_code=1
        )

    try:
        folder_path, backup_name = parse_backup_selector(backup_selector)
    except ValueError:
        return CommandExecuteResponse(
            success=False, output="", error="Invalid backup selector format", exit_code=1
        )

    conn_mgr = ConnectionManager()
    backup_mgr = BackupManager(Path(folder_path))
    backups = backup_mgr.list_backups()
    backup_info = next(
        (b for b in backups if b.get("backup_name", b["name"]) == backup_name), None
    )

    if not backup_info:
        return CommandExecuteResponse(
            success=False, output="", error=f"Backup '{backup_name}' not found", exit_code=1
        )

    backup_path = backup_info["path"]

    connection = conn_mgr.get_connection(connection_name)
    if not connection:
        return CommandExecuteResponse(
            success=False,
            output="",
            error=f"Connection '{connection_name}' not found",
            exit_code=1,
        )

    connection_uri = conn_mgr.repository.build_uri_from_connection(connection)

    try:
        backup_mgr.restore_backup(backup_path, connection_uri, drop_collections)
        drop_msg = " (with --drop flag)" if drop_collections else ""
        return CommandExecuteResponse(
            success=True,
            output=f"✓ Backup '{backup_name}' restored successfully to '{connection_name}'{drop_msg}",
            error=None,
            exit_code=0,
        )
    except Exception as e:
        return CommandExecuteResponse(
            success=False, output="", error=f"Restore failed: {str(e)}", exit_code=1
        )
