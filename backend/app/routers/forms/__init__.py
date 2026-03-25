"""HTTP API endpoints for form management"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Request

from app.core.forms import (
    CONNECT_ADD_FORM,
    CONNECT_REMOVE_FORM,
    CONNECT_LIST_FORM,
    CONNECT_TEST_FORM,
    CONNECT_UPDATE_SELECT_FORM,
    CONNECT_UPDATE_DETAILS_FORM,
    BACKUP_FOLDER_ADD_SELECT_FORM,
    BACKUP_FOLDER_ADD_CONFIGURE_FORM,
    BACKUP_FOLDER_DELETE_SELECT_FORM,
    BACKUP_FOLDER_DELETE_CONFIRM_FORM,
    BACKUP_FOLDER_LIST_FORM,
    BACKUP_CREATE_SELECT_FORM,
    BACKUP_CREATE_CONFIGURE_FORM,
    BACKUP_LIST_FORM,
    BACKUP_DELETE_FORM,
    BACKUP_RESTORE_SELECT_FORM,
    BACKUP_RESTORE_CONFIGURE_FORM,
)
from app.middleware.auth import get_current_user
from app.enums import FormPath
from app.core.utils.paths import normalize_backup_folder_path
from app.core.utils.backup_utils import parse_backup_selector
from app.core.utils.fs import delete_directory_if_exists
from app.routers.forms.connect import (
    build_connection_options_with_date,
    build_connection_options,
    build_connection_list_items,
)
from app.routers.forms.backup_folder import (
    build_backup_folder_connection_options,
    build_backup_folder_delete_options,
    build_backup_folder_list_items,
)
from app.routers.forms.backup_ops import (
    build_backup_create_connection_options,
    build_backup_list_items,
    build_backup_selector_options,
    build_restore_selector_options,
    build_restore_connection_options,
    _format_size,
)

router = APIRouter(prefix="/api/forms", tags=["forms"])

# Registry mapping form paths to their static schema objects
FORM_REGISTRY = {
    FormPath.CONNECT_ADD: CONNECT_ADD_FORM,
    FormPath.CONNECT_REMOVE: CONNECT_REMOVE_FORM,
    FormPath.CONNECT_LIST: CONNECT_LIST_FORM,
    FormPath.CONNECT_TEST: CONNECT_TEST_FORM,
    FormPath.CONNECT_UPDATE_SELECT: CONNECT_UPDATE_SELECT_FORM,
    FormPath.CONNECT_UPDATE_DETAILS: CONNECT_UPDATE_DETAILS_FORM,
    FormPath.BACKUP_FOLDER_ADD_SELECT: BACKUP_FOLDER_ADD_SELECT_FORM,
    FormPath.BACKUP_FOLDER_ADD_CONFIGURE: BACKUP_FOLDER_ADD_CONFIGURE_FORM,
    FormPath.BACKUP_FOLDER_DELETE_SELECT: BACKUP_FOLDER_DELETE_SELECT_FORM,
    FormPath.BACKUP_FOLDER_DELETE_CONFIRM: BACKUP_FOLDER_DELETE_CONFIRM_FORM,
    FormPath.BACKUP_FOLDER_LIST: BACKUP_FOLDER_LIST_FORM,
    FormPath.BACKUP_CREATE_SELECT: BACKUP_CREATE_SELECT_FORM,
    FormPath.BACKUP_CREATE_CONFIGURE: BACKUP_CREATE_CONFIGURE_FORM,
    FormPath.BACKUP_LIST: BACKUP_LIST_FORM,
    FormPath.BACKUP_DELETE: BACKUP_DELETE_FORM,
    FormPath.BACKUP_RESTORE_SELECT: BACKUP_RESTORE_SELECT_FORM,
    FormPath.BACKUP_RESTORE_CONFIGURE: BACKUP_RESTORE_CONFIGURE_FORM,
}


@router.get("/connection-details/{connection_name}")
async def get_connection_details(
    connection_name: str,
    current_user: dict = Depends(get_current_user),
):
    """Get connection details for pre-populating the update form (Step 2).

    Args:
        connection_name: Name of the connection to fetch

    Returns:
        Connection details with parsed URI components

    Raises:
        404: If connection not found
    """
    from app.core.connection_ops import ConnectionManager

    conn_mgr = ConnectionManager()
    connection = conn_mgr.get_connection(connection_name)

    if not connection:
        raise HTTPException(
            status_code=404,
            detail=f"Connection '{connection_name}' not found",
        )

    return {
        "name": connection.get("name", ""),
        "description": connection.get("description", ""),
        "host": connection.get("host", "localhost"),
        "port": connection.get("port", 27017),
        "username": connection.get("username", ""),
        "password": connection.get("password", ""),
        "database": connection.get("database", ""),
        "auth_source": connection.get("auth_source"),
    }


@router.get("/{command_path:path}")
async def get_form_schema(
    command_path: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get form schema for a command, dynamically populated where needed.

    Args:
        command_path: Command path (e.g., "connect/add", "connect/remove")

    Returns:
        Form schema as JSON

    Raises:
        404: If no form exists for the given command
    """
    try:
        form_path = FormPath(command_path)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"No form available for command: {command_path}",
        )

    if form_path not in FORM_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail=f"No form available for command: {command_path}",
        )

    form_schema = FORM_REGISTRY[form_path]

    # ── connect/remove ──────────────────────────────────────────────────────
    if form_path == FormPath.CONNECT_REMOVE:
        from app.core.connection_ops import ConnectionManager

        conn_mgr = ConnectionManager()
        options = build_connection_options_with_date(conn_mgr.list_connections())

        form_dict = form_schema.model_dump(exclude_none=True)
        for field in form_dict.get("fields", []):
            if field["id"] == "connections":
                field["options"] = options
                break
        return form_dict

    # ── connect/list ─────────────────────────────────────────────────────────
    if form_path == FormPath.CONNECT_LIST:
        from app.core.connection_ops import ConnectionManager

        conn_mgr = ConnectionManager()
        items = build_connection_list_items(conn_mgr.list_connections())

        form_dict = form_schema.model_dump(exclude_none=True)
        for field in form_dict.get("fields", []):
            if field["id"] == "connections_list":
                field["items"] = items
                break
        return form_dict

    # ── connect/test ──────────────────────────────────────────────────────────
    if form_path == FormPath.CONNECT_TEST:
        from app.core.connection_ops import ConnectionManager

        conn_mgr = ConnectionManager()
        options = build_connection_options(conn_mgr.list_connections())

        form_dict = form_schema.model_dump(exclude_none=True)
        for field in form_dict.get("fields", []):
            if field["id"] == "connections":
                field["options"] = options
                break
        return form_dict

    # ── connect/update/select ─────────────────────────────────────────────────
    if form_path == FormPath.CONNECT_UPDATE_SELECT:
        from app.core.connection_ops import ConnectionManager

        conn_mgr = ConnectionManager()
        options = build_connection_options(conn_mgr.list_connections())

        form_dict = form_schema.model_dump()
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_name":
                field["options"] = options
                break
        return form_dict

    # ── connect/update/details ────────────────────────────────────────────────
    if form_path == FormPath.CONNECT_UPDATE_DETAILS:
        return form_schema.model_dump()

    # ── backup/folder/add/select ──────────────────────────────────────────────
    if form_path == FormPath.BACKUP_FOLDER_ADD_SELECT:
        from app.core.connection_ops import ConnectionManager

        conn_mgr = ConnectionManager()
        options = build_backup_folder_connection_options(conn_mgr.list_connections())

        form_dict = form_schema.model_dump()
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_name":
                field["options"] = options
                break
        return form_dict

    # ── backup/folder/add/configure ───────────────────────────────────────────
    if form_path == FormPath.BACKUP_FOLDER_ADD_CONFIGURE:
        return form_schema.model_dump()

    # ── backup/folder/delete/select ───────────────────────────────────────────
    if form_path == FormPath.BACKUP_FOLDER_DELETE_SELECT:
        from app.core.connection_ops import ConnectionManager

        conn_mgr = ConnectionManager()
        options = build_backup_folder_delete_options(conn_mgr.list_connections())

        form_dict = form_schema.model_dump()
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_name":
                field["options"] = options
                break
        return form_dict

    # ── backup/folder/delete/confirm ──────────────────────────────────────────
    if form_path == FormPath.BACKUP_FOLDER_DELETE_CONFIRM:
        return form_schema.model_dump()

    # ── backup/folder/list ────────────────────────────────────────────────────
    if form_path == FormPath.BACKUP_FOLDER_LIST:
        from app.core.connection_ops import ConnectionManager

        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()

        filter_options = [{"value": "all", "label": "All Connections"}]
        for conn in connections:
            filter_options.append({"value": conn["name"], "label": conn["name"]})

        form_dict = form_schema.model_dump(exclude_none=True)
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_filter":
                field["options"] = filter_options
            elif field["id"] == "folders_list":
                field["items"] = build_backup_folder_list_items(connections)
        return form_dict

    # ── backup/create/select ──────────────────────────────────────────────────
    if form_path == FormPath.BACKUP_CREATE_SELECT:
        from app.core.connection_ops import ConnectionManager

        conn_mgr = ConnectionManager()
        options = build_backup_create_connection_options(conn_mgr.list_connections())

        form_dict = form_schema.model_dump()
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_name":
                field["options"] = options
                break
        return form_dict

    # ── backup/create/configure ───────────────────────────────────────────────
    if form_path == FormPath.BACKUP_CREATE_CONFIGURE:
        return form_schema.model_dump()

    # ── backup/list ───────────────────────────────────────────────────────────
    if form_path == FormPath.BACKUP_LIST:
        from app.core.connection_ops import ConnectionManager

        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()

        filter_options = [{"value": "all", "label": "All Backups"}]
        for conn in connections:
            filter_options.append({"value": conn["name"], "label": conn["name"]})

        form_dict = form_schema.model_dump(exclude_none=True)
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_filter":
                field["options"] = filter_options
            elif field["id"] == "backups_list":
                field["items"] = build_backup_list_items(connections)
        return form_dict

    # ── backup/delete ─────────────────────────────────────────────────────────
    if form_path == FormPath.BACKUP_DELETE:
        from app.core.connection_ops import ConnectionManager

        conn_mgr = ConnectionManager()
        options = build_backup_selector_options(conn_mgr.list_connections())
        options.sort(key=lambda x: x["label"])

        form_dict = form_schema.model_dump(exclude_none=True)
        for field in form_dict.get("fields", []):
            if field["id"] == "backup_selector":
                field["options"] = options
                break
        return form_dict

    # ── backup/restore/select ─────────────────────────────────────────────────
    if form_path == FormPath.BACKUP_RESTORE_SELECT:
        from app.core.connection_ops import ConnectionManager

        conn_mgr = ConnectionManager()
        options = build_restore_selector_options(conn_mgr.list_connections())

        form_dict = form_schema.model_dump()
        for field in form_dict.get("fields", []):
            if field["id"] == "backup_selector":
                field["options"] = options
                break
        return form_dict

    # ── backup/restore/configure ──────────────────────────────────────────────
    if form_path == FormPath.BACKUP_RESTORE_CONFIGURE:
        from app.core.connection_ops import ConnectionManager
        from app.core.backup_ops import BackupManager

        backup_selector = request.query_params.get("backup_selector")
        if not backup_selector:
            raise HTTPException(
                status_code=400,
                detail="backup_selector query parameter required",
            )

        try:
            folder_path, backup_name = parse_backup_selector(backup_selector)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid backup_selector format"
            )

        backup_mgr = BackupManager(Path(folder_path))
        backups = backup_mgr.list_backups()
        backup_info = next(
            (b for b in backups if b.get("backup_name", b["name"]) == backup_name),
            None,
        )

        if not backup_info:
            raise HTTPException(status_code=404, detail="Backup not found")

        conn_mgr = ConnectionManager()
        connection_options = build_restore_connection_options(
            conn_mgr.list_connections(),
            original_connection=backup_info.get("connection_name"),
        )

        form_dict = form_schema.model_dump(exclude_none=True)
        original_connection = backup_info.get("connection_name")
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_name":
                field["options"] = connection_options
                if original_connection:
                    field["default"] = original_connection
        return form_dict

    # Fallback: return schema as-is
    return form_schema.model_dump(exclude_none=True)


# === POST ENDPOINTS FOR FORM SUBMISSIONS ===

@router.post("/backup/folder/add/configure")
async def submit_backup_folder_add(
    form_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Add a backup folder to a connection (Step 2 submission)."""
    from app.core.connection_ops import ConnectionManager

    try:
        connection_name = form_data.get("connection_name")
        folder_path_input = form_data.get("folder_path")
        create_if_missing = form_data.get("create_if_missing", True)

        if not connection_name or not folder_path_input:
            raise HTTPException(status_code=400, detail="Missing required fields")

        folder_path = normalize_backup_folder_path(folder_path_input)
        path_obj = Path(folder_path)

        if not path_obj.exists():
            if create_if_missing:
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to create folder: {str(e)}",
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Folder does not exist: {folder_path}",
                )

        test_file = path_obj / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Folder is not writable: {str(e)}"
            )

        conn_mgr = ConnectionManager()
        if not conn_mgr.add_backup_path(connection_name, folder_path):
            raise HTTPException(
                status_code=400,
                detail="Failed to add backup path (may already exist or connection not found)",
            )

        return {"success": True, "message": f"Backup folder added: {folder_path}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/folder/delete/confirm")
async def submit_backup_folder_delete(
    form_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Delete a backup folder from a connection (removes DB record + physical directory)."""
    from app.core.connection_ops import ConnectionManager

    try:
        connection_name = form_data.get("connection_name")
        folder_path = form_data.get("folder_path")
        confirmation = form_data.get("confirmation", False)

        if not connection_name or not folder_path:
            raise HTTPException(status_code=400, detail="Missing required fields")

        if not confirmation:
            raise HTTPException(
                status_code=400, detail="You must confirm the deletion"
            )

        conn_mgr = ConnectionManager()
        connection = conn_mgr.get_connection(connection_name)

        if not connection:
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found",
            )

        backup_paths = connection.get("backup_paths", [])
        if folder_path not in backup_paths:
            raise HTTPException(
                status_code=400,
                detail=f"Folder '{folder_path}' is not registered for connection '{connection_name}'",
            )

        if not conn_mgr.remove_backup_path(connection_name, folder_path):
            raise HTTPException(
                status_code=400,
                detail="Failed to remove backup folder from connection",
            )

        try:
            delete_directory_if_exists(folder_path)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Folder removed from config but failed to delete from disk: {str(e)}",
            )

        return {
            "success": True,
            "message": f"Backup folder '{folder_path}' deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/create/configure")
async def submit_backup_create(
    form_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Create a new backup (Step 2 submission)."""
    from app.core.connection_ops import ConnectionManager
    from app.core.backup_ops import BackupManager

    try:
        connection_name = form_data.get("connection_name")
        backup_name = form_data.get("backup_name")
        backup_location = form_data.get("backup_location")

        if not connection_name or not backup_name or not backup_location:
            raise HTTPException(status_code=400, detail="Missing required fields")

        conn_mgr = ConnectionManager()
        connection = conn_mgr.get_connection(connection_name)

        if not connection:
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found",
            )

        backup_paths = connection.get("backup_paths", [])
        if backup_location not in backup_paths:
            raise HTTPException(
                status_code=400,
                detail="Invalid backup location. Must be one of the configured backup folders.",
            )

        connection_uri = conn_mgr.repository.build_uri_from_connection(connection)
        backup_mgr = BackupManager(Path(backup_location))

        try:
            backup_path = backup_mgr.create_backup(
                connection_uri, connection_name, backup_name
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

        return {
            "success": True,
            "message": f"Backup '{backup_name}' created successfully at {backup_path}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/delete")
async def submit_backup_delete(
    form_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Delete a backup."""
    from app.core.backup_ops import BackupManager

    try:
        backup_selector = form_data.get("backup_selector")
        confirmation = form_data.get("confirmation", False)

        if not backup_selector:
            raise HTTPException(status_code=400, detail="No backup selected")

        if not confirmation:
            raise HTTPException(
                status_code=400, detail="You must confirm the deletion"
            )

        try:
            folder_path, backup_name = backup_selector.split("|", 1)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid backup selector format"
            )

        backup_mgr = BackupManager(Path(folder_path))
        backup_mgr.delete_backup(backup_name)

        return {
            "success": True,
            "message": f"Backup '{backup_name}' deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/restore/configure")
async def submit_backup_restore(
    form_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Restore a backup to a connection."""
    from app.core.backup_ops import BackupManager
    from app.core.connection_ops import ConnectionManager
    from app.core.utils.uri_builder import build_mongodb_uri

    try:
        backup_selector = form_data.get("backup_selector")
        connection_name = form_data.get("connection_name")
        drop_collections = form_data.get("drop_collections", True)
        confirmation = form_data.get("confirmation", False)

        if not backup_selector:
            raise HTTPException(status_code=400, detail="No backup selected")
        if not connection_name:
            raise HTTPException(status_code=400, detail="No connection selected")
        if not confirmation:
            raise HTTPException(
                status_code=400, detail="You must confirm the restore operation"
            )

        try:
            folder_path, backup_name = backup_selector.split("|", 1)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid backup selector format"
            )

        backup_mgr = BackupManager(Path(folder_path))
        backups = backup_mgr.list_backups()
        backup_info = next(
            (b for b in backups if b.get("backup_name", b["name"]) == backup_name),
            None,
        )

        if not backup_info:
            raise HTTPException(status_code=404, detail="Backup not found")

        backup_path = backup_info["path"]

        conn_mgr = ConnectionManager()
        connection = conn_mgr.get_connection(connection_name)

        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")

        target_database = connection.get("database")
        if not target_database:
            raise HTTPException(
                status_code=400,
                detail="Connection must have a database specified for restore",
            )

        connection_uri = build_mongodb_uri(
            host=connection.get("host", "localhost"),
            port=connection.get("port", 27017),
            username=connection.get("username"),
            password=connection.get("password"),
            database=target_database,
            auth_source=connection.get("auth_source"),
        )

        try:
            backup_mgr.restore_backup(
                backup_path, connection_uri, target_database, drop_collections
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Restore failed: {str(e)}"
            )

        drop_msg = " (with --drop flag)" if drop_collections else ""
        return {
            "success": True,
            "message": f"Backup '{backup_name}' restored successfully to '{connection_name}'{drop_msg}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
