"""Backup folder command handlers"""

from pathlib import Path
import os

from app.core.connection_ops import ConnectionManager
from app.routers.commands.models import CommandExecuteResponse
from app.core.utils.paths import normalize_backup_folder_path
from app.core.utils.fs import delete_directory_if_exists


def handle_backup_folder_add(params: dict) -> CommandExecuteResponse:
    """Add a backup folder to a connection"""
    connection_name = params.get("connection_name")
    if isinstance(connection_name, list):
        connection_name = connection_name[0] if connection_name else None

    if not connection_name:
        return CommandExecuteResponse(
            success=False, output="", error="No connection selected", exit_code=1
        )

    folder_path_input = params.get("folder_path")
    create_if_missing = params.get("create_if_missing", True)

    if not folder_path_input:
        return CommandExecuteResponse(
            success=False, output="", error="Folder path is required", exit_code=1
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

    folder_path = normalize_backup_folder_path(folder_path_input)
    path_obj = Path(folder_path)

    if not path_obj.exists():
        if create_if_missing:
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return CommandExecuteResponse(
                    success=False,
                    output="",
                    error=f"Failed to create directory: {str(e)}",
                    exit_code=1,
                )
        else:
            return CommandExecuteResponse(
                success=False,
                output="",
                error=f"Path '{folder_path}' does not exist",
                exit_code=1,
            )

    if not os.access(folder_path, os.W_OK):
        return CommandExecuteResponse(
            success=False,
            output="",
            error=f"Path is not writable: {folder_path}",
            exit_code=1,
        )

    if conn_mgr.add_backup_path(connection_name, folder_path):
        return CommandExecuteResponse(
            success=True,
            output=f"✓ Added backup folder: {folder_path}",
            error=None,
            exit_code=0,
        )

    return CommandExecuteResponse(
        success=False,
        output="",
        error="Folder already exists in connection's backup folder list",
        exit_code=1,
    )


def handle_backup_folder_delete(params: dict) -> CommandExecuteResponse:
    """Remove a backup folder from a connection and delete it from disk"""
    connection_name = params.get("connection_name")
    folder_path = params.get("folder_path")
    confirmation = params.get("confirmation", False)

    if not connection_name:
        return CommandExecuteResponse(
            success=False, output="", error="Connection name is required", exit_code=1
        )
    if not folder_path:
        return CommandExecuteResponse(
            success=False, output="", error="Folder path is required", exit_code=1
        )
    if not confirmation:
        return CommandExecuteResponse(
            success=False, output="", error="You must confirm the deletion", exit_code=1
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
    if folder_path not in backup_paths:
        return CommandExecuteResponse(
            success=False,
            output="",
            error=f"Folder '{folder_path}' is not registered for connection '{connection_name}'",
            exit_code=1,
        )

    if not conn_mgr.remove_backup_path(connection_name, folder_path):
        return CommandExecuteResponse(
            success=False,
            output="",
            error="Failed to remove backup folder from connection",
            exit_code=1,
        )

    try:
        delete_directory_if_exists(folder_path)
    except Exception as e:
        return CommandExecuteResponse(
            success=False,
            output="",
            error=f"Folder removed from config but failed to delete from disk: {str(e)}",
            exit_code=1,
        )

    return CommandExecuteResponse(
        success=True,
        output=f"✓ Backup folder '{folder_path}' deleted successfully",
        error=None,
        exit_code=0,
    )
