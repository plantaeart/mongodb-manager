"""HTTP API endpoints for form management"""

from fastapi import APIRouter, HTTPException, Depends, Request
from app.core.form_definitions import (
    CONNECT_ADD_FORM, 
    CONNECT_REMOVE_FORM, 
    CONNECT_LIST_FORM, 
    CONNECT_TEST_FORM,
    CONNECT_UPDATE_SELECT_FORM,
    CONNECT_UPDATE_DETAILS_FORM,
    BACKUP_FOLDER_ADD_SELECT_FORM,
    BACKUP_FOLDER_ADD_CONFIGURE_FORM,
    BACKUP_FOLDER_LIST_FORM,
    BACKUP_CREATE_SELECT_FORM,
    BACKUP_CREATE_CONFIGURE_FORM,
    BACKUP_LIST_FORM,
    BACKUP_DELETE_FORM,
    BACKUP_RESTORE_SELECT_FORM,
    BACKUP_RESTORE_CONFIGURE_FORM
)
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/forms", tags=["forms"])

# Registry mapping command paths to form schemas
FORM_REGISTRY = {
    "connect/add": CONNECT_ADD_FORM,
    "connect/remove": CONNECT_REMOVE_FORM,
    "connect/list": CONNECT_LIST_FORM,
    "connect/test": CONNECT_TEST_FORM,
    "connect/update/select": CONNECT_UPDATE_SELECT_FORM,
    "connect/update/details": CONNECT_UPDATE_DETAILS_FORM,
    
    # Backup management forms (multi-step)
    "backup/folder/add/select": BACKUP_FOLDER_ADD_SELECT_FORM,
    "backup/folder/add/configure": BACKUP_FOLDER_ADD_CONFIGURE_FORM,
    "backup/folder/list": BACKUP_FOLDER_LIST_FORM,
    "backup/create/select": BACKUP_CREATE_SELECT_FORM,
    "backup/create/configure": BACKUP_CREATE_CONFIGURE_FORM,
    "backup/list": BACKUP_LIST_FORM,
    "backup/delete": BACKUP_DELETE_FORM,
    "backup/restore/select": BACKUP_RESTORE_SELECT_FORM,
    "backup/restore/configure": BACKUP_RESTORE_CONFIGURE_FORM,
}


@router.get("/connection-details/{connection_name}")
async def get_connection_details(
    connection_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Get connection details for pre-populating update form (Step 2)
    
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
            detail=f"Connection '{connection_name}' not found"
        )
    
    # Return connection components directly (no URI parsing needed!)
    return {
        "name": connection.get("name", ""),
        "description": connection.get("description", ""),
        "host": connection.get("host", "localhost"),
        "port": connection.get("port", 27017),
        "username": connection.get("username", ""),
        "password": connection.get("password", ""),
        "database": connection.get("database", ""),
        "auth_source": connection.get("auth_source", "admin")
    }


@router.get("/{command_path:path}")
async def get_form_schema(
    command_path: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get form schema for a command
    
    Args:
        command_path: Command path (e.g., "connect/add", "connect/remove")
        
    Returns:
        Form schema as JSON
        
    Examples:
        GET /api/forms/connect/add -> Returns CONNECT_ADD_FORM schema
        GET /api/forms/connect/remove -> Returns CONNECT_REMOVE_FORM with populated connections
        
    Raises:
        404: If no form exists for the given command
    """
    if command_path not in FORM_REGISTRY:
        raise HTTPException(
            status_code=404, 
            detail=f"No form available for command: {command_path}"
        )
    
    form_schema = FORM_REGISTRY[command_path]
    
    # Special handling for connect/remove: populate connection options dynamically
    if command_path == "connect/remove":
        from app.core.connection_ops import ConnectionManager
        from app.core.utils.uri_builder import build_mongodb_uri_masked
        from datetime import datetime
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        # Build options from connections
        options = []
        for conn in connections:
            # Build masked URI from components
            uri_display = build_mongodb_uri_masked(
                host=conn.get("host", "localhost"),
                port=conn.get("port", 27017),
                username=conn.get("username"),
                database=conn.get("database"),
                auth_source=conn.get("auth_source", "admin")
            )
            desc = conn.get("description", "")
            added_at = conn.get("added_at", "")
            
            # Format added_at if available
            date_display = ""
            if added_at:
                try:
                    dt = datetime.fromisoformat(added_at.replace("Z", "+00:00"))
                    date_display = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    date_display = added_at
            
            options.append({
                "value": conn["name"],
                "label": conn["name"],
                "description": desc or uri_display,
                "metadata": {
                    "uri": uri_display,
                    "description": desc,
                    "added_at": date_display
                }
            })
        
        # Create a copy of the form schema and populate options
        form_dict = form_schema.dict(exclude_none=True)
        
        # Find the connections field and populate options
        for field in form_dict.get("fields", []):
            if field["id"] == "connections":
                field["options"] = options
                break
        
        return form_dict
    
    # Special handling for connect/list: populate connection items
    if command_path == "connect/list":
        from app.core.connection_ops import ConnectionManager
        from app.core.utils.uri_builder import build_mongodb_uri_masked
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        # Create a copy of the form schema
        form_dict = form_schema.dict(exclude_none=True)
        
        # Build items array with connection data
        items = []
        for conn in connections:
            # Build masked URI from components
            masked_uri = build_mongodb_uri_masked(
                host=conn.get("host", "localhost"),
                port=conn.get("port", 27017),
                username=conn.get("username"),
                database=conn.get("database"),
                auth_source=conn.get("auth_source", "admin")
            )
            
            items.append({
                "name": conn["name"],
                "uri": masked_uri,
                "description": conn.get("description", ""),
                "added_at": conn.get("added_at", "")
            })
        
        # Update the list field with items
        for field in form_dict.get("fields", []):
            if field["id"] == "connections_list":
                field["items"] = items
                break
        
        return form_dict
    
    # Special handling for connect/test: populate connection options for checkbox-list
    if command_path == "connect/test":
        from app.core.connection_ops import ConnectionManager
        from app.core.utils.uri_builder import build_mongodb_uri_masked
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        form_dict = form_schema.dict(exclude_none=True)
        
        # Build options from connections
        options = []
        for conn in connections:
            # Build masked URI from components
            uri_display = build_mongodb_uri_masked(
                host=conn.get("host", "localhost"),
                port=conn.get("port", 27017),
                username=conn.get("username"),
                database=conn.get("database"),
                auth_source=conn.get("auth_source", "admin")
            )
            desc = conn.get("description", "")
            
            options.append({
                "value": conn["name"],
                "label": conn["name"],
                "description": desc or uri_display,
                "metadata": {
                    "uri": uri_display,
                    "description": desc
                }
            })
        
        # Update the checkbox-list field with options
        for field in form_dict.get("fields", []):
            if field["id"] == "connections":
                field["options"] = options
                break
        
        return form_dict
    
    # Special handling for connect/update/select: populate connection options for Step 1
    if command_path == "connect/update/select":
        from app.core.connection_ops import ConnectionManager
        from app.core.utils.uri_builder import build_mongodb_uri_masked
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        form_dict = form_schema.dict(exclude_none=True)
        
        # Build connection options for selector
        options = []
        for conn in connections:
            # Build masked URI from components
            uri_display = build_mongodb_uri_masked(
                host=conn.get("host", "localhost"),
                port=conn.get("port", 27017),
                username=conn.get("username"),
                database=conn.get("database"),
                auth_source=conn.get("auth_source", "admin")
            )
            desc = conn.get("description", "")
            
            options.append({
                "value": conn["name"],
                "label": conn["name"],
                "description": desc or uri_display,
                "metadata": {
                    "uri": uri_display,
                    "description": desc
                }
            })
        
        # Populate connection selector options
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_name":
                field["options"] = options
                break
        
        return form_dict
    
    # Special handling for connect/update/details: Step 2 form (no dynamic data needed here)
    if command_path == "connect/update/details":
        # This form will be pre-populated by frontend when connection is selected
        return form_schema.dict(exclude_none=True)
    
    # === BACKUP FOLDER FORMS ===
    
    # Special handling for backup/folder/add/select: populate connection options for Step 2
    if command_path == "backup/folder/add/select":
        from app.core.connection_ops import ConnectionManager
        from app.core.utils.uri_builder import build_mongodb_uri_masked
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        form_dict = form_schema.dict(exclude_none=True)
        
        # Build connection options with masked URI for display
        options = []
        for conn in connections:
            # Build masked URI from components
            masked_uri = build_mongodb_uri_masked(
                host=conn.get("host", "localhost"),
                port=conn.get("port", 27017),
                username=conn.get("username"),
                database=conn.get("database"),
                auth_source=conn.get("auth_source", "admin")
            )
            
            options.append({
                "value": conn["name"],
                "label": conn["name"],
                "description": masked_uri,
                "metadata": {
                    "user_description": conn.get("description", "")
                }
            })
        
        # Update the connection selector field
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_name":
                field["options"] = options
                break
        
        return form_dict
    
    # Special handling for backup/folder/add/configure: Step 1 form (no dynamic data needed)
    if command_path == "backup/folder/add/configure":
        return form_schema.dict(exclude_none=True)
    
    # Special handling for backup/folder/list: populate filter and folder list
    if command_path == "backup/folder/list":
        from app.core.connection_ops import ConnectionManager
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        form_dict = form_schema.dict(exclude_none=True)
        
        # Build connection filter options
        filter_options = [{"value": "all", "label": "All Connections"}]
        for conn in connections:
            filter_options.append({
                "value": conn["name"],
                "label": conn["name"]
            })
        
        # Build folders list
        folders_items = []
        for conn in connections:
            backup_paths = conn.get("backup_paths", [])
            active_path = conn.get("active_backup_path")
            
            if backup_paths:
                folders_items.append({
                    "connection_name": conn["name"],
                    "description": conn.get("description", ""),
                    "backup_paths": backup_paths,
                    "active_backup_path": active_path
                })
        
        # Update form fields
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_filter":
                field["options"] = filter_options
            elif field["id"] == "folders_list":
                field["items"] = folders_items
        
        return form_dict
    
    # === BACKUP OPERATION FORMS ===
    
    # Special handling for backup/create/select: populate connections with backup_paths for Step 1
    if command_path == "backup/create/select":
        from app.core.connection_ops import ConnectionManager
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        form_dict = form_schema.dict(exclude_none=True)
        
        # Build options - only connections with backup paths
        options = []
        for conn in connections:
            backup_paths = conn.get("backup_paths", [])
            active_path = conn.get("active_backup_path")
            
            if backup_paths:
                # Show active path in description if available
                description = f"Backup paths: {len(backup_paths)}"
                if active_path:
                    description += f" (Active: {active_path})"
                
                options.append({
                    "value": conn["name"],
                    "label": conn["name"],
                    "description": description,
                    "metadata": {
                        "backup_paths": backup_paths,
                        "active_backup_path": active_path
                    }
                })
        
        # Update connection selector field
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_name":
                field["options"] = options
                break
        
        return form_dict
    
    # Special handling for backup/create/configure: Step 2 form (no dynamic data needed)
    if command_path == "backup/create/configure":
        return form_schema.dict(exclude_none=True)
    
    # Special handling for backup/list: populate filter and backup list
    if command_path == "backup/list":
        from app.core.connection_ops import ConnectionManager
        from app.core.backup_ops import BackupManager
        from pathlib import Path
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        form_dict = form_schema.dict(exclude_none=True)
        
        # Build connection filter options
        filter_options = [{"value": "all", "label": "All Backups"}]
        for conn in connections:
            filter_options.append({
                "value": conn["name"],
                "label": conn["name"]
            })
        
        # Collect all backups from all connections
        all_backups = []
        for conn in connections:
            backup_paths = conn.get("backup_paths", [])
            for backup_path in backup_paths:
                backup_mgr = BackupManager(Path(backup_path))
                backups = backup_mgr.list_backups()
                
                for backup in backups:
                    # Calculate size
                    backup_size = 0
                    try:
                        for item in Path(backup["path"]).rglob("*"):
                            if item.is_file():
                                backup_size += item.stat().st_size
                    except:
                        backup_size = 0
                    
                    # Format size
                    size_str = _format_size(backup_size)
                    
                    all_backups.append({
                        "backup_name": backup.get("backup_name", backup["name"]),
                        "connection_name": backup["connection_name"],
                        "created_at": backup.get("created_at", ""),
                        "databases": backup.get("databases", []),
                        "size": size_str,
                        "folder_path": str(backup_path)
                    })
        
        # Sort by created_at descending
        all_backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Update form fields
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_filter":
                field["options"] = filter_options
            elif field["id"] == "backups_list":
                field["items"] = all_backups
        
        return form_dict
    
    # Special handling for backup/delete: populate backup selector
    if command_path == "backup/delete":
        from app.core.connection_ops import ConnectionManager
        from app.core.backup_ops import BackupManager
        from pathlib import Path
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        form_dict = form_schema.dict(exclude_none=True)
        
        # Collect all backups with composite key
        options = []
        for conn in connections:
            backup_paths = conn.get("backup_paths", [])
            for backup_path in backup_paths:
                backup_mgr = BackupManager(Path(backup_path))
                backups = backup_mgr.list_backups()
                
                for backup in backups:
                    backup_name = backup.get("backup_name", backup["name"])
                    created_at = backup.get("created_at", "")
                    
                    # Composite key: folder_path|backup_name
                    composite_key = f"{backup_path}|{backup_name}"
                    
                    options.append({
                        "value": composite_key,
                        "label": f"{backup_name} ({conn['name']})",
                        "description": f"Created: {created_at}",
                        "metadata": {
                            "folder_path": backup_path,
                            "backup_name": backup_name,
                            "connection_name": conn["name"]
                        }
                    })
        
        # Sort by label
        options.sort(key=lambda x: x["label"])
        
        # Update backup selector field
        for field in form_dict.get("fields", []):
            if field["id"] == "backup_selector":
                field["options"] = options
                break
        
        return form_dict
    
    # Special handling for backup/restore/select: populate backup selector (Step 1)
    if command_path == "backup/restore/select":
        from app.core.connection_ops import ConnectionManager
        from app.core.backup_ops import BackupManager
        from pathlib import Path
        
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        form_dict = form_schema.dict(exclude_none=True)
        
        # Collect all backups with composite key
        options = []
        for conn in connections:
            backup_paths = conn.get("backup_paths", [])
            for backup_path in backup_paths:
                backup_mgr = BackupManager(Path(backup_path))
                backups = backup_mgr.list_backups()
                
                for backup in backups:
                    backup_name = backup.get("backup_name", backup["name"])
                    created_at = backup.get("created_at", "")
                    size = backup.get("size", 0)
                    databases = backup.get("databases", [])
                    
                    # Composite key: folder_path|backup_name
                    composite_key = f"{backup_path}|{backup_name}"
                    
                    # Format label with details
                    size_str = _format_size(size) if size else "Unknown"
                    db_count = len(databases) if isinstance(databases, list) else 0
                    
                    options.append({
                        "value": composite_key,
                        "label": f"{backup_name} ({conn['name']}) - {size_str}",
                        "description": f"Created: {created_at} | {db_count} database(s)",
                        "metadata": {
                            "folder_path": backup_path,
                            "backup_name": backup_name,
                            "connection_name": conn["name"],
                            "size": size,
                            "databases": databases,
                            "created_at": created_at
                        }
                    })
        
        # Sort by creation date (newest first)
        options.sort(key=lambda x: x["metadata"].get("created_at", ""), reverse=True)
        
        # Update backup selector field
        for field in form_dict.get("fields", []):
            if field["id"] == "backup_selector":
                field["options"] = options
                break
        
        return form_dict
    
    # Special handling for backup/restore/configure: populate connection selector (Step 2)
    if command_path == "backup/restore/configure":
        from app.core.connection_ops import ConnectionManager
        from app.core.backup_ops import BackupManager
        from app.core.utils.uri_builder import build_mongodb_uri_masked
        from pathlib import Path
        
        # Get backup_selector from query params
        backup_selector = request.query_params.get("backup_selector")
        if not backup_selector:
            raise HTTPException(status_code=400, detail="backup_selector query parameter required")
        
        # Parse composite key
        try:
            folder_path, backup_name = backup_selector.split("|", 1)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid backup_selector format")
        
        # Get backup metadata
        backup_mgr = BackupManager(Path(folder_path))
        backups = backup_mgr.list_backups()
        backup_info = next((b for b in backups if b.get("backup_name", b["name"]) == backup_name), None)
        
        if not backup_info:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        # Get connections
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        form_dict = form_schema.dict(exclude_none=True)
        
        # Build connection options
        connection_options = []
        original_connection = backup_info.get("connection_name")
        
        for conn in connections:
            masked_uri = build_mongodb_uri_masked(
                host=conn.get("host", "localhost"),
                port=conn.get("port", 27017),
                username=conn.get("username"),
                database=conn.get("database"),
                auth_source=conn.get("auth_source", "admin")
            )
            
            connection_options.append({
                "value": conn["name"],
                "label": f"{conn['name']} ({masked_uri})",
                "description": conn.get("description", ""),
                "metadata": {
                    "is_original": conn["name"] == original_connection
                }
            })
        
        # Sort: original connection first, then alphabetically
        connection_options.sort(key=lambda x: (not x["metadata"]["is_original"], x["label"]))
        
        # Update form fields
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_name":
                field["options"] = connection_options
                # Set default to original connection if available
                if original_connection:
                    field["default"] = original_connection
        
        return form_dict
    
    # Convert Pydantic model to dict for JSON response
    return form_schema.dict(exclude_none=True)


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 GB")
    """
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


# === POST ENDPOINTS FOR FORM SUBMISSIONS ===

@router.post("/backup/folder/add/configure")
async def submit_backup_folder_add(
    form_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Add a backup folder to a connection (Step 2 submission)
    
    Args:
        form_data: Form submission data with connection_name, folder_path, create_if_missing, set_as_active
        
    Returns:
        Success message or error
    """
    from app.core.connection_ops import ConnectionManager
    from app.core.utils.config import BACKUP_FOLDER_SUFFIX, BACKUP_BASE_DIR
    from pathlib import Path
    import os
    
    try:
        connection_name = form_data.get("connection_name")
        folder_path_input = form_data.get("folder_path")
        create_if_missing = form_data.get("create_if_missing", True)
        set_as_active = form_data.get("set_as_active", True)
        
        if not connection_name or not folder_path_input:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Clean the input path (remove leading/trailing slashes and whitespace)
        clean_path = folder_path_input.strip().strip('/')
        
        # Enforce base directory prefix: mongodb-manager-backups/
        # If user already included it, don't duplicate
        if clean_path.startswith(BACKUP_BASE_DIR):
            # Remove the base dir prefix temporarily for processing
            clean_path = clean_path[len(BACKUP_BASE_DIR):].strip('/')
        
        # Construct full path: mongodb-manager-backups/user-input_mongodb_manager
        folder_path_base = f"{BACKUP_BASE_DIR}/{clean_path}"
        
        # Automatically append suffix if not already present
        if not folder_path_base.endswith(BACKUP_FOLDER_SUFFIX):
            folder_path = f"{folder_path_base}{BACKUP_FOLDER_SUFFIX}"
        else:
            folder_path = folder_path_base
        
        # Check if folder exists or create it
        path_obj = Path(folder_path)
        if not path_obj.exists():
            if create_if_missing:
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to create folder: {str(e)}"
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Folder does not exist: {folder_path}"
                )
        
        # Test write permissions
        test_file = path_obj / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Folder is not writable: {str(e)}"
            )
        
        # Add backup path to connection
        conn_mgr = ConnectionManager()
        success = conn_mgr.add_backup_path(connection_name, folder_path)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to add backup path (may already exist or connection not found)"
            )
        
        # Set as active if requested or if it's the first path
        connection = conn_mgr.get_connection(connection_name)
        if connection and (set_as_active or len(connection.get("backup_paths", [])) == 1):
            conn_mgr.set_active_backup_path(connection_name, folder_path)
        
        return {
            "success": True,
            "message": f"Backup folder added: {folder_path}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/create/configure")
async def submit_backup_create(
    form_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a new backup (Step 2 submission)
    
    Args:
        form_data: Form submission data with connection_name, backup_name, backup_location
        
    Returns:
        Success message or error
    """
    from app.core.connection_ops import ConnectionManager
    from app.core.backup_ops import BackupManager
    from pathlib import Path
    
    try:
        connection_name = form_data.get("connection_name")
        backup_name = form_data.get("backup_name")
        backup_location = form_data.get("backup_location")
        
        if not connection_name or not backup_name or not backup_location:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Get connection
        conn_mgr = ConnectionManager()
        connection = conn_mgr.get_connection(connection_name)
        
        if not connection:
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        # Verify backup_location is in the connection's backup_paths
        backup_paths = connection.get("backup_paths", [])
        if backup_location not in backup_paths:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid backup location. Must be one of the configured backup folders."
            )
        
        # Build URI from connection components
        connection_uri = conn_mgr.repository.build_uri_from_connection(connection)
        
        # Create backup
        backup_mgr = BackupManager(Path(backup_location))
        
        try:
            backup_path = backup_mgr.create_backup(
                connection_uri,
                connection_name,
                backup_name
            )
        except ValueError as e:
            # Duplicate backup name or invalid name
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            # mongodump failed
            raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")
        
        return {
            "success": True,
            "message": f"Backup '{backup_name}' created successfully at {backup_path}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/delete")
async def submit_backup_delete(
    form_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Delete a backup
    
    Args:
        form_data: Form submission data with backup_selector (composite key), confirmation
        
    Returns:
        Success message or error
    """
    from app.core.backup_ops import BackupManager
    from pathlib import Path
    
    try:
        backup_selector = form_data.get("backup_selector")
        confirmation = form_data.get("confirmation", False)
        
        if not backup_selector:
            raise HTTPException(status_code=400, detail="No backup selected")
        
        if not confirmation:
            raise HTTPException(
                status_code=400,
                detail="You must confirm the deletion"
            )
        
        # Parse composite key: folder_path|backup_name
        try:
            folder_path, backup_name = backup_selector.split("|", 1)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid backup selector format"
            )
        
        # Delete backup
        backup_mgr = BackupManager(Path(folder_path))
        backup_mgr.delete_backup(backup_name)
        
        return {
            "success": True,
            "message": f"Backup '{backup_name}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/restore/configure")
async def submit_backup_restore(
    form_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Restore a backup to a connection
    
    Args:
        form_data: Form submission data with backup_selector, connection_name, drop_collections, confirmation
        
    Returns:
        Success message or error
    """
    from app.core.backup_ops import BackupManager
    from app.core.connection_ops import ConnectionManager
    from app.core.utils.uri_builder import build_mongodb_uri
    from pathlib import Path
    
    try:
        backup_selector = form_data.get("backup_selector")
        connection_name = form_data.get("connection_name")
        drop_collections = form_data.get("drop_collections", True)  # Default to True for proper restore
        confirmation = form_data.get("confirmation", False)
        
        if not backup_selector:
            raise HTTPException(status_code=400, detail="No backup selected")
        
        if not connection_name:
            raise HTTPException(status_code=400, detail="No connection selected")
        
        if not confirmation:
            raise HTTPException(
                status_code=400,
                detail="You must confirm the restore operation"
            )
        
        # Parse composite key: folder_path|backup_name
        try:
            folder_path, backup_name = backup_selector.split("|", 1)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid backup selector format"
            )
        
        # Get backup path
        backup_mgr = BackupManager(Path(folder_path))
        backups = backup_mgr.list_backups()
        backup_info = next((b for b in backups if b.get("backup_name", b["name"]) == backup_name), None)
        
        if not backup_info:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        backup_path = backup_info["path"]
        
        # Get connection and build URI
        conn_mgr = ConnectionManager()
        connection = conn_mgr.get_connection(connection_name)
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Get database name from connection
        target_database = connection.get("database")
        
        if not target_database:
            raise HTTPException(
                status_code=400, 
                detail="Connection must have a database specified for restore"
            )
        
        connection_uri = build_mongodb_uri(
            host=connection.get("host", "localhost"),
            port=connection.get("port", 27017),
            username=connection.get("username"),
            password=connection.get("password"),
            database=target_database,
            auth_source=connection.get("auth_source", "admin")
        )
        
        # Perform restore
        try:
            backup_mgr.restore_backup(backup_path, connection_uri, target_database, drop_collections)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")
        
        drop_msg = " (with --drop flag)" if drop_collections else ""
        return {
            "success": True,
            "message": f"Backup '{backup_name}' restored successfully to '{connection_name}'{drop_msg}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

